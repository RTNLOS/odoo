# -*- coding: utf-8 -*-

from odoo import models

class Journal(models.Model):
    _inherit='account.journal'

    #Fix the Odoo change to Balance in GL
    def _fill_bank_cash_dashboard_data(self, dashboard_data):
        """Populate all bank and cash journal's data dict with relevant information for the kanban card."""
        bank_cash_journals = self.filtered(lambda journal: journal.type in ('bank', 'cash'))
        if not bank_cash_journals:
            return

        # Number to reconcile
        self._cr.execute("""
            SELECT st_line_move.journal_id,
                   COUNT(st_line.id)
              FROM account_bank_statement_line st_line
              JOIN account_move st_line_move ON st_line_move.id = st_line.move_id
             WHERE st_line_move.journal_id IN %s
               AND NOT st_line.is_reconciled
               AND st_line_move.to_check IS NOT TRUE
               AND st_line_move.state = 'posted'
          GROUP BY st_line_move.journal_id
        """, [tuple(bank_cash_journals.ids)])
        number_to_reconcile = {
            journal_id: count
            for journal_id, count in self.env.cr.fetchall()
        }

        # Last statement
        self.env.cr.execute("""
            SELECT journal.id, statement.id
              FROM account_journal journal
         LEFT JOIN LATERAL (
                      SELECT id
                        FROM account_bank_statement
                       WHERE journal_id = journal.id
                    ORDER BY first_line_index DESC
                       LIMIT 1
                   ) statement ON TRUE
             WHERE journal.id = ANY(%s)
        """, [self.ids])
        last_statements = {journal_id: statement_id for journal_id, statement_id in self.env.cr.fetchall()}
        self.env['account.bank.statement'].browse(i for i in last_statements.values() if i).mapped('balance_end_real')  # prefetch

        outstanding_pay_account_balances = bank_cash_journals._get_journal_dashboard_outstanding_payments()

        # To check
        to_check = {
            res['journal_id'][0]: (res['amount'], res['journal_id_count'])
            for res in self.env['account.bank.statement.line'].read_group(
                domain=[
                    ('journal_id', 'in', bank_cash_journals.ids),
                    ('move_id.to_check', '=', True),
                    ('move_id.state', '=', 'posted'),
                ],
                fields=['amount'],
                groupby=['journal_id'],
            )
        }

        for journal in bank_cash_journals:
            last_statement = self.env['account.bank.statement'].browse(last_statements.get(journal.id))
            currency = journal.currency_id or journal.company_id.currency_id
            has_outstanding, outstanding_pay_account_balance = outstanding_pay_account_balances[journal.id]
            to_check_balance, number_to_check = to_check.get(journal.id, (0, 0))
            if journal.currency_id:
                query = f"""
                    SELECT SUM(amount_currency) 
                    FROM account_move_line where account_id = {journal.default_account_id.id}
                """
            else:
                query = f"""
                    SELECT SUM(balance) 
                    FROM account_move_line where account_id = {journal.default_account_id.id}
                """

            self.env.cr.execute(query)
            account_balance = self.env.cr.fetchall()
            
            dashboard_data[journal.id].update({
                'number_to_check': number_to_check,
                'to_check_balance': currency.format(to_check_balance),
                'number_to_reconcile': number_to_reconcile.get(journal.id, 0),
                'account_balance': currency.format(account_balance[0][0]) if account_balance[0][0] else 0.0,
                #'has_at_least_one_statement': bool(last_statement),
                'has_at_least_one_statement': True,
                'nb_lines_bank_account_balance': True,
                #'nb_lines_bank_account_balance': bool(journal.has_statement_lines),
                'outstanding_pay_account_balance': currency.format(outstanding_pay_account_balance),
                'nb_lines_outstanding_pay_account_balance': has_outstanding,
                'last_balance': currency.format(last_statement.balance_end_real),
                'bank_statements_source': journal.bank_statements_source,
                'is_sample_data': journal.has_statement_lines,
            })