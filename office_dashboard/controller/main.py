# -*- coding: utf-8 -*-
import base64
import json
import logging
import random
from multiprocessing.spawn import prepare
import urllib.parse
from odoo import http, fields
from odoo.exceptions import ValidationError
from odoo.tools import consteq, plaintext2html
from odoo.http import request
from datetime import date, datetime, timedelta
import datetime as DT
import calendar
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import odoo
import odoo.addons.web.controllers.home as main
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url, is_user_internal
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)
# Shared parameters for all login/signup flows


class MainOfficeDashboard(http.Controller):
    
    def get_memo_last_stage(self, memo):
        '''used to return file that are in closed stage'''
        last_stage_ids = None
        memo_setting_last_stage_ids = memo.memo_setting_id and memo.memo_setting_id[0].stage_ids
        if memo_setting_last_stage_ids:
            last_stage_ids = memo_setting_last_stage_ids
        return last_stage_ids
        
    @http.route([
        "/my-dashboard"
        ], type='http', auth='user', website=True, website_published=True)
    def myDashboard(self):
        vals = self.office_dashboard()
        _logger.info(vals)
        return request.render("office_dashboard.office_dashboard_template_id", qcontext=vals)
               
    def office_dashboard(
        self, 
        memo_type_param=[], 
        search_request=False, 
        kwargs={}):

        domain = [('active', '=', True), ('memo_project_type', 'in', ['warehouse', 'procurement', 'agency', 'cfwd', 'transport', 'travel'])]
        project_file_type = []
        currency_name = kwargs.get('currency_name') or 'NGN'
        _logger.info(f'what is currency {currency_name}')
        if search_request:
            domain += [
                '|', ('code', '=ilike', search_request),
                 ('name', 'ilike', search_request)]
        if kwargs.get('project_file_type'):
            project_file_type = [int(kwargs.get('project_file_type'))]
            domain += [('memo_type', 'in', project_file_type)]
            
        if kwargs.get('project_file_category_type'): # e.g cfwd, agency, transport etc
            project_file_category_type = kwargs.get('project_file_category_type')
            domain += [('memo_project_type', '=', project_file_category_type)]
            
        if kwargs.get('customer_name'):
            customer_ids = [int(kwargs.get('customer_name'))]
            domain += [('client_id', 'in', customer_ids)]
            
        if kwargs.get('month') or kwargs.get('year'):
            month_domain = self.get_memo_with_month_year(kwargs.get('month'), kwargs.get('year'))
            domain += month_domain #
        today_date = fields.Date.today()
        past_seven_days = today_date + relativedelta(days=-7) # 
        past_one_month = today_date + relativedelta(months=-30) # 
        past_seven_days = datetime.strptime(past_seven_days.strftime('%Y%m%d'), '%Y%m%d')
        current_datetime = datetime.strptime(today_date.strftime('%Y%m%d'), '%Y%m%d')
        past_week_domain = domain + [
            ('date', '>=', past_seven_days),
            ('date', '<=', current_datetime),
            ]
        past_one_month_domain = domain + [
            ('date', '>=', past_one_month),
            ('date', '<=', current_datetime),
            ('state', 'in', ['Done', 'Approve2','Approve'])
            ]
        
        ongoing_domain = domain + [
            ('state', 'not in', ['Done', 'Approve2','Approve']),
            ]
        
        expected_document_domain = domain + [
            ('state', 'not in', ['Done', 'Approve2','Approve']),
            ]
        # output_opened_file_domain = domain + [('state', 'not in', ['Done', 'Approve2'])]
        
        output_opened_file_domain = domain + [('state', 'not in', ['Done', 'Approve2'])]
         
         
        today_date = fields.Date.today()
        total_number_invoices_not_closed = 0
        memo_invoices_closed_ids = []
        invoice_unclose_ids = []
        
        total_invoiced_revenue = 0.00
        budget_revenue_total = 0.00
        total_paid_invoiced_revenue = 0.00
        total_budget_cost = 0.00
        total_paid_cost, total_invoice_cost= 0.00, 0.00
        draft_lead_memo = domain + [('state', 'in', ['submit'])]
        # draft_lead_memo_ids = request.env["memo.model"].sudo().search(draft_lead_memo)
        # domain += [('state', 'not in', ['submit'])]
        memo_invoice_ids = request.env["memo.model"].sudo().search(domain)
        _logger.info(f"MY DOMAIN IS WHAT {domain}")
        task_not_done, additional_po_process = 0, 0
        
        project_x_data = []
        budget_amount_project_y_data = []
        revenue_amount_project_y_data = []
        month_sales_project_x_data = []
        project_element = []
        
        customer_project_items_name= []
        customer_project_items = []
        usd_budget_amount_project_y_datac = []
        usd_revenue_amount_project_y_datac = []
        budget_amount_project_y_datac = []
        revenue_amount_project_y_datac = []
        customer_project_dicts = {}
        
        grouped_customer_info = []
        opened_file_ids, closed_file_ids = [], []
        to_be_invoiced_ids = []
        past_one_week_ids, past_two_week_ids, past_one_month_ids = [], [], []
        
        files_to_be_closeds = []
        files_to_be_approveds = []
        
        so_payment_not_registereds = []
        pos_to_be_approved_ids = []
        files_wto_cost = []
        files_wto_rev = []
        # po_to_be_validateds = []
        # invoices_to_be_validateds = []
        project_dicts = {}
        wip_project_dicts = {}
        wip_grand_total_dicts = {}
        wip_booked_project_dicts = {}
        wip_booked_grand_total_dicts = {}
        
        wip_paid_project_dicts = {}
        wip_paid_grand_total_dicts = {}
        
        wip_balance_project_dicts = {}
        wip_balance_grand_total_dicts = {}
        
        wip_grouped_dicts = {}
        pos_to_be_paid_ids = []
        if memo_invoice_ids:
            _logger.info(f'what is inc {memo_invoice_ids[0:2]}')
            
            #### adding doughnut_filter_project_type_data
            project_items = list(set([mm.memo_type.memo_key for mm in memo_invoice_ids])) if kwargs.get('project_file_type') else list(set([mm.memo_project_type for mm in memo_invoice_ids]))
            # wip_memo_types = list(set([mm.memo_type.memo_key for mm in memo_invoice_ids])) if kwargs.get('project_file_type') else list(set([mm.memo_project_type for mm in memo_invoice_ids]))
            # used to compute the grand total of each dicts 
            wip_grand_total_dicts = {
                    'name': 'Total', 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }
            wip_booked_grand_total_dicts = {
                    'name': 'Total', 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }
            wip_paid_grand_total_dicts = {
                    'name': 'Total', 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }

            wip_balance_grand_total_dicts = {
                    'name': 'Total', 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }

            for pupdate in project_items:
                project_dicts[f'{pupdate}'] = {
                    'revenue_total': 0.00, 
                    'budget_total': 0.00, 
                    'month_sales': None,
                    'usd_revenue_total': 0.00,
                    'usd_budget_total': 0.00,
                }
                
                wip_grouped_dicts[f'{pupdate}'] = {
                    'name': pupdate, 
                    'total': 0,
                    'record_ids': []
                }
                wip_project_dicts[f'{pupdate}'] = {
                    'name': pupdate, 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }
                wip_booked_project_dicts[f'{pupdate}'] = {
                    'name': pupdate, 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }
                wip_paid_project_dicts[f'{pupdate}'] = {
                    'name': pupdate, 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }
                wip_balance_project_dicts[f'{pupdate}'] = {
                    'name': pupdate, 
                    'wip_revenue': 0, 
                    'wip_cost': 0, 
                    'margin': 0, 
                }
                
            _logger.info(f'FINAL WIP DATA ARE == {wip_project_dicts}')
            customer_project_items = list(set([mm.client_id.id for mm in memo_invoice_ids]))
            customer_project_items_name = list(set([mm.client_id.name for mm in memo_invoice_ids]))
            for cupdate in customer_project_items:
                customer_project_dicts[f'{cupdate}'] = {
                    'name': request.env['res.partner'].browse([cupdate]).name, 
                    'revenue_total': 0.00, 
                    'budget_total': 0.00,
                    'usd_revenue_total': 0.00,
                    'usd_budget_total': 0.00,
                }
            for mo in memo_invoice_ids:
                # .filtered(lambda mt:mt.memo_project_type == 'memo_project_type'): #[0:5]: 
                mtype = mo.memo_project_type if not kwargs.get('project_file_type') else mo.memo_type.memo_key
                po_budget_ids = mo.mapped('po_ids')
                so_budget_ids = mo.mapped('so_ids')
                # mtype = rec.memo_type.memo_key
                ######  BUILD WIP
                
                ########## computing the long overdue files 
                last_stage_id = self.get_memo_last_stage(mo)
                if mo.stage_id.id == last_stage_id[-2].id: 
                    files_to_be_closeds.append(mo.id)
                # CLOSED FILES    
                if mo.stage_id.stage_type in ['closed']:# or mo.stage_id.id == last_stage_id[-1].id: # determine if the file is at closed stage
                    closed_file_ids.append(mo.id)
                    if mo.memo_project_type == 'agency':
                        _logger.info(f"CLOSED AGENECY {mo.id}")
                # OPENED FILES
                else:
                    if mo.memo_project_type == 'agency':
                        _logger.info(f"OPENED AGENECY {mo.id}")
                    opened_file_ids.append(mo.id) # determine if the file is not at closed stage
                    #### WIP OPENED FILES
                    record_items = wip_grouped_dicts.get(f'{mtype}').get('record_ids')
                    record_items.append(mo.id)
                    wip_grouped_dicts.get(f'{mtype}').update({
                    'name': mtype, 
                    'total': wip_grouped_dicts.get(mtype).get('total') + 1,
                    # 'record_ids': [], 
                    'record_ids': record_items   
                    })
                    _logger.info(f"SITER {type(record_items)} ==> {record_items} --> {wip_grouped_dicts}-====>  {wip_grouped_dicts.get(f'{mtype}')}")
                    
                    if record_items and type(record_items) == list:
                        its = record_items + [mo.id]
                        wip_grouped_dicts.get(f'{mtype}').update({
                            'record_ids': its
                        })
                    # WIP CALCULATIONS
                    wip_revenue_total, wip_confirmed_revenue_total, wip_paid_revenue = self.compute_so_naira_dollar_value(mo.so_ids, 'USD') if currency_name in ['USD'] else \
                    self.compute_so_naira_dollar_value(mo.so_ids, 'NGN')
                    _logger.info(f'UPDATE MTYPE WIP DATA ARE == {wip_project_dicts.get(mtype)}')
                    
                    wip_po_computes = self.compute_po_naira_dollar_value(mo.po_ids, 'NGN') if currency_name in ['NGN'] else self.compute_po_naira_dollar_value(po_budget_ids, 'USD')
                    wip_cost_total = wip_po_computes[0]
                    wip_margin = wip_revenue_total - wip_cost_total # difference in revenue and cost wip
                    
                    # WIP GRAND TOTAL
                    wip_grand_total_dicts.update({
                        'wip_revenue': wip_grand_total_dicts.get('wip_revenue') + wip_revenue_total,
                        'wip_cost': wip_grand_total_dicts.get('wip_cost') + wip_cost_total,
                        'margin': wip_grand_total_dicts.get('margin') + wip_margin,
                    }) 
                    
                    wip_project_dicts.get(f'{mtype}').update({
                    'name':mtype, 
                    'wip_revenue': wip_project_dicts.get(mtype).get('wip_revenue') + wip_revenue_total,
                    'wip_cost': wip_project_dicts.get(mtype).get('wip_cost') + wip_po_computes[0],
                    'margin': wip_project_dicts.get(mtype).get('margin') + wip_margin,
                    })
                    
                    wip_booked_cost_total = wip_po_computes[1]
                    wip_booked_margin = wip_confirmed_revenue_total - wip_booked_cost_total # difference in revenue and cost wip
                    
                    wip_booked_project_dicts.get(f'{mtype}').update({
                    'name':mtype, 
                    'wip_revenue': wip_booked_project_dicts.get(mtype).get('wip_revenue') + wip_confirmed_revenue_total,
                    'wip_cost': wip_booked_project_dicts.get(mtype).get('wip_cost') + wip_booked_cost_total,
                    'margin': wip_booked_project_dicts.get(mtype).get('margin') + wip_booked_margin,
                    })
                    # WIP_DATA.append(wip_project_dicts);
                    _logger.info(f'UPDATE WIP DATA ARE == {wip_project_dicts}')
                    
                    # GRAND TOTAL
                    wip_booked_grand_total_dicts.update({
                        'wip_revenue': wip_booked_grand_total_dicts.get('wip_revenue') + wip_confirmed_revenue_total,
                        'wip_cost': wip_booked_grand_total_dicts.get('wip_cost') + wip_booked_cost_total,
                        'margin': wip_booked_grand_total_dicts.get('margin') + wip_booked_margin,
                    })
                    wip_paid_cost_total = wip_po_computes[2]
                    wip_paid_margin = wip_paid_revenue - wip_paid_cost_total # difference in revenue and cost wip
                    
                    wip_paid_project_dicts.get(f'{mtype}').update({
                    'name':mtype, 
                    'wip_revenue': wip_paid_project_dicts.get(mtype).get('wip_revenue') + wip_paid_revenue,
                    'wip_cost': wip_paid_project_dicts.get(mtype).get('wip_cost') + wip_paid_cost_total,
                    'margin': wip_paid_project_dicts.get(mtype).get('margin') + wip_paid_margin,
                    })
                    # WIP_DATA.append(wip_project_dicts);
                    _logger.info(f'UPDATE WIP PAID DATA ARE == {wip_paid_project_dicts}')
                    # GRAND TOTAL
                    wip_paid_grand_total_dicts.update({
                        'wip_revenue': wip_paid_grand_total_dicts.get('wip_revenue') + wip_paid_revenue,
                        'wip_cost': wip_paid_grand_total_dicts.get('wip_cost') + wip_paid_cost_total,
                        'margin': wip_paid_grand_total_dicts.get('margin') + wip_paid_margin,
                    })
                    
                    wip_balance_revenue = wip_revenue_total - wip_paid_revenue
                    wip_balance_cost = wip_cost_total - wip_po_computes[1]
                    wip_balance_revenue_cost_margin = wip_revenue_total - wip_paid_revenue
                     
                    wip_balance_project_dicts.get(f'{mtype}').update({
                    'name':mtype, 
                    'wip_revenue': wip_balance_project_dicts.get(mtype).get('wip_revenue') + wip_balance_revenue,
                    'wip_cost': wip_balance_project_dicts.get(mtype).get('wip_cost') + wip_balance_cost,
                    'margin': wip_balance_project_dicts.get(mtype).get('margin') + wip_balance_revenue_cost_margin,
                    })
                    
                    # GRAND TOTAL
                    wip_balance_grand_total_dicts.update({
                        'wip_revenue': wip_balance_grand_total_dicts.get('wip_revenue') + wip_balance_revenue,
                        'wip_cost': wip_balance_grand_total_dicts.get('wip_cost') + wip_balance_cost,
                        'margin': wip_balance_grand_total_dicts.get('margin') + wip_balance_revenue_cost_margin,
                    })
                    # WIP CALCULATION ends
                    
                    #################### computing overdue files
                    task_date_difference = 0 
                    if mo.task_start_date:
                        task_date_difference = today_date - mo.task_start_date
                        task_date_difference = task_date_difference.days
                    date_difference = today_date - mo.date.date()
                    if date_difference.days in range (0, 7):
                        past_one_week_ids.append(mo.id)
                    elif date_difference.days in range (8, 30):
                        past_two_week_ids.append(mo.id)
                        
                    if task_date_difference > 30:
                        past_one_month_ids.append(mo.id)
                    _logger.info(f"files not close {mo.id} stage tye {mo.stage_id.stage_type}")
                    if mo.stage_id.stage_type not in ['normal','', False, 'invoice_check', 'validate_invoice', 'close']:
                        # any stage aside normal and closed
                        # if mo.state not in ['submit','refuse']: what was there before it was changed
                        closed_so_ids = mo.mapped('so_ids').filtered(
                        lambda st: st.invoice_status in ['invoiced'] or st.state in ['sale'])
                        if closed_so_ids:
                            invoice_unclose_ids += [mo.id]
                        _logger.info(f"List of invoices not unclosed {mo.id}")
                    if mo.stage_id.stage_type in ['validate_invoice']:
                        # if mo.po_ids and not mo.so_ids: what was the before
                        to_be_invoiced_ids.append(mo.id) # to be invoiced
                        
                    if mo.stage_id.stage_type in ['file_check']:
                        # Files without Cost Budget: files in file checks without PO AND SOs
                        if not mo.po_ids:
                            # files not with po_ids
                            files_wto_cost.append(mo.id)
                        if not mo.so_ids:
                            # files not with so_ids
                            files_wto_rev.append(mo.id)
                    
                    if mo.stage_id.is_approved_stage: # to be approved
                        files_to_be_approveds.append(mo.id)
                        
                    if mo.mapped('so_ids').filtered(lambda s: s.state in ['sale'] and s.invoice_status not in ['invoiced']):
                        # if any sale order payment not registered in accounts
                        so_payment_not_registereds.append(mo.id)
                 
                    if mo.mapped('po_ids').filtered(lambda s: s.state in ['purchase', 'done'] and s.invoice_status not in ['invoiced']):
                        # if any sale order payment not registered in accounts
                        pos_to_be_paid_ids.append(mo.id) # po to be paid
                    
                    if mo.mapped('po_memo_ids'):
                        po_memo_to_be_approved = mo.mapped('po_memo_ids').filtered(
                            lambda st: st.stage_id.is_approved_stage
                        )
                        if po_memo_to_be_approved:
                            pos_to_be_approved_ids.append(mo.id) 
                    
                    # if mo.mapped('po_ids').filtered(lambda s: s.state in ['draft']):
                    #     # if any sale order payment not registered in accounts
                    #     pos_to_be_approved_ids.append(mo.id) 
                    # if mo.mapped('po_memo_ids').memo_setting_id and mo.mapped('po_memo_ids').memo_setting_id.stage_ids:
                        # po_memo_stage_ids = mo.mapped('po_memo_ids').memo_setting_id.stage_ids[-2]
                        # first_last_stage_ids = list(po_memo_stage_ids[0].id, po_memo_stage_ids[-1].id)
                        # po_memo_not_to_be_approved = mo.mapped('po_memo_ids').filtered(
                            # lambda s: s.stage_id.id not in first_last_stage_ids
                        # ) # meaning they are in approval stage
                             
                #### adding doughnut_filter_project_type_data
                
                rec_revenue_months = list(set([r.date_order.strftime('%b') for r in mo.mapped('so_ids').filtered(lambda so: so.state not in ['draft', 'cancel'])]))
                revenue_total, budget_total, usd_revenue_total, usd_budget_total = 0, 0, 0, 0
                
                budget_rev_total, invoice_rev_total, invoice_paid_rev = self.compute_so_naira_dollar_value(mo.so_ids, 'USD') if currency_name in ['USD'] else \
                    self.compute_so_naira_dollar_value(mo.so_ids, 'NGN')
                budget_total = budget_rev_total
                revenue_total = invoice_rev_total
                
                budget_project_total = project_dicts.get(f'{mtype}').get('budget_total') + budget_total
                revenue_project_total = project_dicts.get(f'{mtype}').get('revenue_total') + revenue_total
                project_dicts.get(f'{mtype}').update({
                    'revenue_total':revenue_project_total, 
                    'budget_total':budget_project_total,
                    'month_sales': rec_revenue_months,
                    'client_id': mo.client_id.name#  if 'customer_name' in kwargs else '',
                    })
                project_element.append(project_dicts)
                
                #########################
                
                
                revenue_totalc, budget_totalc, usd_revenue_totalc, usd_budget_totalc = 0.00,0.00,0.00,0.00 
                budget_revenue_total += budget_rev_total
                total_invoiced_revenue += invoice_rev_total
                total_paid_invoiced_revenue += invoice_paid_rev
                
                budget_totalc = budget_rev_total
                revenue_totalc = invoice_rev_total
                    
                budget_project_totalc = customer_project_dicts.get(f'{mo.client_id.id}').get('budget_total') + budget_totalc
                revenue_project_totalc = customer_project_dicts.get(f'{mo.client_id.id}').get('revenue_total') + revenue_totalc
                
                usd_revenue_project_totalc = customer_project_dicts.get(f'{mo.client_id.id}').get('usd_revenue_total') + usd_revenue_totalc
                usd_budget_project_totalc = customer_project_dicts.get(f'{mo.client_id.id}').get('usd_budget_total') + usd_budget_totalc
                customer_project_dicts.get(f'{mo.client_id.id}').update({
                    'revenue_total': revenue_project_totalc, 
                    'budget_total':budget_project_totalc,
                    'usd_revenue_project_total':usd_revenue_project_totalc,
                    'usd_budget_project_total':usd_budget_project_totalc,
                    })
                ##########################################group_customer_info ################
                
                grouped_customer_info.append(self.grouped_customer_info(mo))
                #######################################
                
                # COMPUTES TOTAL OF TASKS NOT COMPLETED FOR THE RECORDS
                task_not_done += len(mo.mapped('memo_sub_stage_ids').filtered(lambda nd: not nd.sub_stage_done)) 
                additional_po_process += len(mo.mapped('po_memo_ids').filtered(lambda nd: nd.state in ['Sent'])) 
                
                
                '''Total Budget revenue: Get all the PO_IDS total amount'''
                if po_budget_ids:
                    po_computes = self.compute_po_naira_dollar_value(po_budget_ids, 'NGN') if currency_name in ['NGN'] else self.compute_po_naira_dollar_value(po_budget_ids, 'USD')
                    '''return total_po_costs, total_invoiced_cost, total_paid_cost'''
                    total_budget_cost += po_computes[0]
                    total_invoice_cost += po_computes[1]
                    total_paid_cost += po_computes[2]
            total_number_invoices_not_closed += len(invoice_unclose_ids)
            ########################################
            project_x_data = [r.capitalize().split('_')[0] for r in list(project_dicts.keys())]
            for k, v in project_dicts.items():
                revenue_amount_project_y_data.append(project_dicts.get(f'{k}').get('revenue_total'))
                budget_amount_project_y_data.append(project_dicts.get(f'{k}').get('budget_total'))
                month_sales_project_x_data.append(project_dicts.get(f'{k}').get('month_sales'))
                
            #############################################
            
            ####################
            for k, v in customer_project_dicts.items():
                revenue_amount_project_y_datac.append(customer_project_dicts.get(f'{k}').get('revenue_total'))
                budget_amount_project_y_datac.append(customer_project_dicts.get(f'{k}').get('budget_total'))
                usd_revenue_amount_project_y_datac.append(customer_project_dicts.get(f'{k}').get('usd_revenue_project_total'))
                usd_budget_amount_project_y_datac.append(customer_project_dicts.get(f'{k}').get('usd_budget_project_total'))
            
            ###################
                
        total_revenue_balance = total_invoiced_revenue - total_paid_invoiced_revenue
        # count_past_week_memo = request.env["memo.model"].sudo().search_count(past_week_domain) 
        count_ongoing_memo = request.env["memo.model"].sudo().search(ongoing_domain)  
        count_ongoing_memo1, count_ongoing_memo2 = self.count_ongoing_memo(count_ongoing_memo)
        get_sales_by_month1, get_sales_by_month2 = self.get_sales_by_month(kwargs)
        _logger.info(f'To be Invoiced ===> {to_be_invoiced_ids} , {len(to_be_invoiced_ids)}, {str(to_be_invoiced_ids)}')
        _logger.info(f'MAIN WIP DATA ARE == {wip_project_dicts}')
        vals = {
            "output_opened_files": {'count': len(opened_file_ids), 'records': str(opened_file_ids)},
            "to_be_invoiced": {'count': len(to_be_invoiced_ids), 'records': str(to_be_invoiced_ids)},
            "to_be_closed_invoiced": {'count': total_number_invoices_not_closed, 'records': str(invoice_unclose_ids)},
            "closed_invoiced": {'count': len(closed_file_ids), 'records': str(closed_file_ids)},
            "past_one_week_ids": {'count': len(past_one_week_ids), 'records': str(past_one_week_ids)},
            "past_two_week_ids": {'count': len(past_two_week_ids), 'records': str(past_two_week_ids)},
            "past_one_month_ids": {'count': len(past_one_month_ids), 'records': str(past_one_month_ids)},
            
            "files_to_be_closeds": {'count': len(files_to_be_closeds), 'records': str(files_to_be_closeds)},
            "files_to_be_approveds": {'count': len(files_to_be_approveds), 'records': str(files_to_be_approveds)},
            "so_payment_not_registereds": {'count': len(so_payment_not_registereds), 'records': str(so_payment_not_registereds)},
            "pos_to_be_approved_ids": {'count': len(pos_to_be_approved_ids), 'records': str(pos_to_be_approved_ids)},
            "files_wto_cost": {'count': len(files_wto_cost), 'records': str(files_wto_cost)},
            "files_wto_rev": {'count': len(files_wto_rev), 'records': str(files_wto_rev)},
            "pos_to_be_paid_ids": {'count': len(pos_to_be_paid_ids), 'records': str(pos_to_be_paid_ids)},
            
            "total_invoiced_revenue": round(total_invoiced_revenue, 2),
            "total_budget": total_budget_cost,
            "booked_budget_cost": total_invoice_cost,
            "paid_budget_cost": total_paid_cost,
            "balance_budget_cost": float(total_invoice_cost - total_paid_cost),
            "budget_revenue_total": round(budget_revenue_total, 2),
            "total_paid_invoiced_revenue": round(total_paid_invoiced_revenue, 2),
            "total_revenue_balance": round(total_revenue_balance, 2),
            "memo_filters": self.get_memo_filters(domain),
            "frame_agreement_ids": request.env['memo.frame.agreement'].search([('active', '=', True)]),
            'calendar_event': self.get_calender_event(),
            "group_project_table": grouped_customer_info, #self.grouped_customer_info(self.search_domain(kwargs=kwargs)),
            "line_doughnut_filter":  json.dumps({
                'project_type_name': project_x_data, # line_doughnut_filter_project_type_data1 or '[]',
                'project_budget':budget_amount_project_y_data, #line_doughnut_filter_project_type_data2 or '[]',
                'project_revenue': revenue_amount_project_y_data, # line_doughnut_filter_project_type_data3 or '[]',
                'month_label': get_sales_by_month1 or '[]',
                'month_sales_amount': get_sales_by_month2 or '[]',
                'customer_name': customer_project_items_name, # line_doughnut_filter_customer_data1 or '[]',
                'customer_budget': budget_amount_project_y_data, # line_doughnut_filter_customer_data2 or '[]',
                'customer_revenue': revenue_amount_project_y_data, #line_doughnut_filter_customer_data3 or '[]',
                'project_counter_item': count_ongoing_memo1,
                'project_counter': count_ongoing_memo2,
            }),
            # "y_data_chart": json.dumps({'data': y_axis_data or '[]'}),
            # "x_data_chart": json.dumps({'data': self.get_xy_data(memo_type_param)[1] or '[]'}),
            "wipGroupData": wip_grouped_dicts, 
            "wipTotalData": wip_project_dicts, 
            "wipTotalGrandData": wip_grand_total_dicts, 
            
            "wipBookedData": wip_booked_project_dicts,
            "wipBookedGrandTotalData": wip_booked_grand_total_dicts, 
            
            "wipPaidData": wip_paid_project_dicts,
            "wipPaidGrandTotalData": wip_paid_grand_total_dicts, 
             
            "wipBalanceData": wip_balance_project_dicts, 
            "wipGrandBalanceData": wip_balance_grand_total_dicts, 
            
            "y_data_chart": json.dumps({'data': '[]'}),
            "x_data_chart": json.dumps({'data': '[]'}),
            # "memo_ids": completed_memo_past_one_month,
            "draft_lead_memo": 0,# len(draft_lead_memo_ids),
            "task_not_done": 0, #task_not_done,
            "additional_po_process": 0, #additional_po_process,
            "count_past_week_memo": 0, #count_past_week_memo,
            "memo_completed_past_one_month": 0, #len(completed_memo_past_one_month),
            "memo_types": request.env['memo.type'].search([('active', '=', True)]),
            "request_item": {
                'new_request':  0,
                'project_pipeline': 20,
                'expected_customers_to_pay': [], # returns list
                },
            "max_progress": 0, #max(y_axis_data) if y_axis_data else 0,
            # FRAME AGREEMENT DATA 
            'frame_agreement_x': [], 
            'frame_agreement_y': [], 
            'frame_agreement_fill': [], 
            'confirmed_so': 0, 
            'all_so': 0,
            'currency_symbol': '$' if currency_name in ['USD'] else '₦',
            'frame_agreement_budget': 0.00
        }
        # frame_agree_agreement = self.dynamic_frame_agreement(self.search_domain(kwargs=kwargs), kwargs)
        # vals.update(frame_agree_agreement)
        _logger.info('zenzenbe ===>', vals)
        return vals
    
    def get_memo_with_frame_agreement(self, fr_id):
        memo_ids = []
        memo_frame_ids = request.env['memo.model'].search([('frame_agreement_ids', '!=', False)])
        for rec in memo_frame_ids:
            fr = rec.mapped('frame_agreement_ids').filtered(
                lambda f: f.id == fr_id
            )
            if fr:
                memo_ids.append(rec.id)
        domain = [('id', 'in', memo_ids)] if memo_ids else False
        return domain 
     
    def get_memo_with_month_year(self, month=False, year=False):
        memo_months = request.env['memo.model'].search([])
        memo_ids = []
        curr_year = fields.Date.today()
        if month and not year:

            memo_ids = [r.id for r in memo_months if r.date and r.date.strftime('%Y') == curr_year.year and r.date.strftime('%b') == month]
            _logger.info(f"MONTH AND CURRENT of {month} and YEAR {year} == > {memo_ids}")

        elif year and not month:
            # year = year else fields.Date.today().year
            memo_ids = [r.id for r in memo_months if r.date and r.date.strftime('%Y') == year] 
            _logger.info(f"YEAR WITHOUT MONTH {month} and YEAR {type(year)} == >  {memo_ids}")
        elif year and month:
            memo_ids = [r.id for r in memo_months if r.date and r.date.strftime('%b') == month and r.date.strftime('%Y') == year]
            _logger.info(f"MONTH AND YEAR MEMO {month} and YEAR {year}  ===> {memo_ids}")
        else:
            memo_ids = []
        domain = [('id', 'in', memo_ids)]
        return domain 
    
    @http.route(['/get-data-info/<string:items>'], type='http', auth='user', website=True)
    def get_data_info(self, items):
        """items : '[8,88,90,70]' """
        # domain="%5B%28%27id%27%2C%20%27in%27%2C%20%5B1%2C%203%2C%204%2C%205%5D%29%5D"
        action_id = request.env.ref('office_dashboard.internal_memo_model_dashboard_action')
        menu_id = request.env.ref('company_memo.internal_memo_menu_model_main2')
        action_window_id = request.env['ir.actions.act_window'].search([
            ('id', '=', action_id.id)
        ], limit=1)
        if action_window_id:
            action_window_id.update({
                'domain': [('id', 'in', eval(items))]
                })
        url = f"/web#action={action_id.id}&model=memo.model&view_type=list&cids=1&menu_id={menu_id.id}"
        return request.redirect(url)

    def get_calender_event(self):
        today_date = fields.Date.today()
        return {
            'curr_month': today_date.strftime('%b'), 
            'curr_year': today_date.year, 
            'all_months': [rec[0:3] for rec in list(calendar.month_name)]
        }
        
    def get_memo_filters(self, domain):
        #, project_file_type=False):
        
        '''params: project_file_type (list) 
        returns memo_dicts.customer_ids(lists of name,), 
        yeat_ids: list of years, projects: object 
        of existing projects, company_ids'''
        # domain=[('active', '=', True)]
        # if project_file_type:
        #     domain + [('memo_type', 'in', project_file_type)]
        memos = request.env['memo.model'].search(domain)
        _logger.info(f"List of all {[me.id for me in memos]}")
        memo_dicts = {
                'project_ids': [{
                    'id': me.id,
                    'name': me.name,
                } for me in set(memos.mapped('memo_type'))],
                'customer_ids': [{
                    'id': me.id,
                    'name': me.name,
                } for me in set(memos.mapped('client_id'))],
                # 'customer_ids': list(set([me.client_id.name for me in memos])),
                'year_ids': list(set([me.date.year for me in memos])),
                'month_ids': list(set([me.date.strftime('%b') for me in memos])),
                'company_ids': [{
                    'id': me.id,
                    'name': me.name,
                } for me in request.env['res.company'].search([])],
            }
        _logger.info(f"MEME MO {memo_dicts}")
        return memo_dicts
     
    def count_ongoing_memo(self, count_ongoing_memo):
        proj_dicts = {}
        for count, var in enumerate(count_ongoing_memo):
            memo_type = var.memo_type.memo_key
            if memo_type not in proj_dicts.keys():
                proj_dicts.update({f'{memo_type}': {}})
                if 'count' not in proj_dicts.keys():
                    proj_dicts[f'{memo_type}'].update({'count': 0})
            memo_type_count = proj_dicts.get(f'{memo_type}').get('count') + 1
            proj_dicts.get(f'{memo_type}').update({
                'count': memo_type_count
            })
        project_list = list(proj_dicts.keys())
        project_counts = [r.get('count') for r in proj_dicts.values()]
        return project_list, project_counts
            
    def search_domain(self, kwargs={}):
        '''kwargs.get('memo_type_param') can be procurement_request
        or memo type key'''
        domain = [('active', '=', True)] 
        # project_file_type = ['agency', 'cwfd', 'procurement', 'travel', 'warehouse', 'transport']
         
        if kwargs.get('project_file_type'):
            domain += [('memo_type', '=', int(kwargs.get('project_file_type')))]
        if kwargs.get('customer_name', None):
            domain += [('client_id', '=', int(kwargs.get('customer_name')))]
        # if kwargs.get('code', None):
        #     domain += [('code', '=ilike', kwargs.get('code'))]
        if kwargs.get('date_from') and kwargs.get('date_to'):
            # date_from, date_to = kwargs.get('date_from', "06/03/2024") and kwargs.get('date_to', "06/07/2024")
            date_from, date_to = kwargs.get('date_from', "06/03/2024") and kwargs.get('date_to', "06/07/2024")
            if date_from and date_to:
                df = datetime.strptime(kwargs.get("date_from"), "%m/%d/%Y")
                dt = datetime.strptime(kwargs.get("date_to"), "%m/%d/%Y")
                domain += [('date', '>=', df), ('date', '<=', dt)]
        return domain
    
    def grouped_customer_info(self, memo, last_index=10):
        # records, count = [], 1
        rev_total = self.compute_revenue_total(memo)
        val = {
            'count': 0,
            'project_name': f"{memo.code or ''} - {memo.name or ''}",
            'customer_name': memo.client_id.name or '',
            'ng_revenue_total': rev_total[0],
            'usd_revenue_total':rev_total[1],
            'ng_budget_total': self.compute_budget_total(memo), 
            'usd_budget_total': self.compute_usd_budget_total(memo),
            }
        return val 
    
    def compute_revenue_total(self, memo_obj):
        ng_revenue_total, usd_revenue_total = 0, 0 
        ng_revenue_total += self.compute_so_naira_dollar_value(memo_obj.so_ids, 'NGN')[0]
        usd_revenue_total += self.compute_so_naira_dollar_value(memo_obj.so_ids, 'USD')[0] 
        return ng_revenue_total, usd_revenue_total 
    
    def compute_budget_total(self, memo_obj):
        ng_budget_total = self.compute_po_naira_dollar_value(memo_obj.po_ids, 'NGN')
        # ng_budget_total = sum([r.amount_total for r in memo_obj.mapped('po_ids')])
        return ng_budget_total[0]
    
    def compute_usd_budget_total(self, memo_obj):
        usd_budget_total = self.compute_po_naira_dollar_value(memo_obj.po_ids, 'USD') 
        return usd_budget_total[0]
    
    def get_month_deals(kwargs={}):
        today = fields.Date.today() 
        today_month = fields.Date.today().month # e.g 9
        current_year = today.year or kwargs.get('current_year', today.year) # 2024
        jan_period = DT.date(current_year, 1, 1) 
        jan_period = jan_period.month or 1
        dic_item = {}
        header = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 
            ]
        for dtm in range(jan_period, today_month+1): # range(1, 10) jan, sept
            # 0
            dtm = dtm - 1 # 1 - 0 = 0
            val = header[dtm] # header[0] = Jan
            dic_item.update({
                f'{val}': 0
            })
        return dic_item
    
    # def compute_memo_periodic_filter(self, memo_obj, month=False, year=False):
    #     '''Used to compute the memo records based on the year, month, filter'''
    #     if month and not year:
    #         p_memo_ids = memo_obj.filtered(lambda r: r.memo_project_type == m_type and len(r.so_ids.ids) > 0) # [{}, {}]
    #         so_ids = pm.mapped('so_ids').filtered(lambda s: s.date_order.strftime("%b") == month and s.date_order.strftime("%Y") == today_year)
    #         _logger.info(f"this sale: 1 {so_ids}")
    #     if year and not month:
    #         so_ids = pm.mapped('so_ids').filtered(lambda s: s.date_order.strftime("%Y") == year)
    #         _logger.info(f"this sale: 2 {so_ids}")
    #     if year and month:
    #         so_ids = pm.mapped('so_ids').filtered(lambda s: s.date_order.strftime("%b") == month and s.date_order.strftime('%Y') == year)
    #         _logger.info(f"this sale: 3 {so_ids}")
    
    def dynamic_mmr_table(self,domain, kwargs=None):
        memo_obj = request.env['memo.model'].search(domain)
        records = []
        # new_items = {'S/N': '', 'Company': request.env.user.company_id.name, 'Department': ''}
        new_items = {'Department': ''}
        # items = {**new_items, **self.get_month_deals()} 
        memo_project_type = set(memo_obj.mapped('memo_project_type')) #i.e 'payment', 'travel', 'cfwd'
        currency_name = kwargs.get('currency_name')
        overall_po_cost = 0
        _logger.info(f"Check Memo records ==> domainx {domain} and {memo_obj} ")
        today_year = fields.Date.today()
        header_item = ['Department', 'Margin'] 
        for m_type in memo_project_type: # eg ['transport', 'agency', 'travel']
            if m_type != False:
                result = {}
                month_items = {**self.get_month_deals()} # {'Jan': 0, 'Feb': 0 ....} .... 
                if kwargs.get('month') or kwargs.get('year'):
                    # filter all within current year
                    p_memo_ids = memo_obj.filtered(
                        lambda r: r.memo_project_type == m_type and r.closing_date != False and r.closing_date.strftime('%Y') == kwargs.get('year')
                        )
                else:
                    p_memo_ids = memo_obj.filtered(
                        lambda r: r.memo_project_type == m_type and r.closing_date != False and r.closing_date.strftime('%Y') == str(today_year.year)
                        )
                _logger.info(f"get naira/dollar value of the Projects => {p_memo_ids} {[self.compute_po_naira_dollar_value(pm.po_ids, currency_name)[1] for pm in p_memo_ids]}")
                month, year = kwargs.get('month'), kwargs.get('year') 
                # [word for sentence in text for word in sentence]
                
                monthly_totals = month_items # {'Jan': 0,} .... # {'Department': '', 'Jan': 0, ..... }
                for pm in p_memo_ids: #  [143, 134, 411]  # 
                    _logger.info(f"the prepared file=> {monthly_totals}")
                    total_po_cost = 0
                    sum_po_ids = self.compute_po_naira_dollar_value(pm.po_ids) if currency_name in ['NGN'] else \
                        self.compute_po_naira_dollar_value(pm.po_ids, 'USD')
                    total_po_cost = sum_po_ids[1]
                    _logger.info(f"SUM OF PM total cost==> {pm.id} === {total_po_cost}")
                    _logger.info(f"Check what SO of {m_type} is : PMSS => {p_memo_ids} {[self.compute_so_naira_dollar_value(pm.so_ids, currency_name)[2] for pm in p_memo_ids]}")
                    budget_rev_total, invoice_revenue_total, invoice_paid_revenue = self.compute_so_naira_dollar_value(pm.so_ids, 'USD') if currency_name in ['USD'] else \
                            self.compute_so_naira_dollar_value(pm.so_ids, 'NGN')
                    margin_sum = invoice_revenue_total - total_po_cost # total revenue of the - total of all so ids 
                    _logger.info(f"MARGIN REVENUE AND PO COST SUM ==> {pm.id} ==> SOOOO ==> {pm.so_ids} =={[p.amount_total for p in pm.so_ids]}= {invoice_revenue_total} - {total_po_cost}====> {margin_sum}")
                    #  if not kwargs.get('paidInvoice')== "Paid" else invoice_paid_revenue 

                    # filter the month of the closing date
                    sale_month = pm.closing_date.strftime("%b") # e.g 'Jan or 'Dec' 
                    if sale_month not in monthly_totals:
                        # monthly_totals = {'Jan': 0.0, 'Feb': 500.00}
                        monthly_totals[sale_month] = margin_sum
                    else:
                        monthly_totals[sale_month] += margin_sum
                monthly_totals = {**new_items, **monthly_totals} # add dictionary 1 and dictionary 2 # {'Jan': 0,} .... # {'Department': '', 'Jan': 0, .......}
                _logger.info(f"MONTHLY TOTALS = {monthly_totals}")
                result[m_type] = monthly_totals
                margin_total = 0

                # Done because of some lazy python issues 
                #result= {'cfwd': {'Department': '', 'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 270500.0, 
                # 'Jun': 0, 'Jul': 0, 'Aug': 0, 'Sep': 48000.0, 'Oct': 0, 'Nov': 36000.0}} 
                
                for ky, vl in result.items():
                    for ki, vi in vl.items():
                        header_item.append(ki) # this will append all the keys ['Department', 'Jan', Feb', 'Margin']
                        # 'i.e {'Department': '', 'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 270500.0, 
                        # 'Jun': 0, 'Jul': 0, 'Aug': 0, 'Sep': 48000.0, 'Oct': 0, 'Nov': 36000.0}
                        
                        # COMPUTE MARGIN DIFFERENT FROM FILE TOTAL COST
                        # if ki not in ['S/N','Company', 'Department']:
                        if ki not in ['Department']:
                            margin_total += vi
                # total_margin = margin_total - total_po_cost # difference in revenue and cost
                result.get(m_type).update({
                        'Department': m_type.capitalize() if m_type else '',
                        'Margin': margin_total,
                        # 'Margin': total_margin
                        })# ("%.2f" % margin_total)
                # {'Jan': 0,} .... # {'Department': '', 'Jan': 0, ....... 'SubTotal': 0, 'Margin': 0}
                records.append(result)
                _logger.info(f"What is the value of Recordsxxx {records}")

        if records:
            ## get the records and looped through to see all the keys in each department 
            all_month_headers = [] #['Department', 'Mar', 'Apr', 'jun', 'Dec', 'Margin']
            for rec in records:
                for rec_key, rec_val in rec.items():
                    # res = rec_val.keys() # Jan, Mar, Aug ... etc
                    all_month_headers += list(dict.fromkeys(rec_val))#['Department', 'Mar', 'Apr']

            ordered_list = [
                'Department', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov','Dec', 'Margin']
            headers = list(set(all_month_headers))
            _logger.info(f"headers xvx {headers}")
            # arrange the list to orderlist
            given_dict = {item: True for item in headers}
            # Prepare the result list in the order of ordered_list 

            new_headers = [item for item in ordered_list if item in given_dict]
            new_records = []
            # Rearrange each department dictionary to match the desired key order 
            for record in records:
                for department, data in record.items(): 
                    for key in new_headers:
                        if key not in data:
                            data[key] = 0  # Set missing months to 0

                    # Rearrange the keys in the desired order
                    record[department] = {key: data[key] for key in new_headers}
                    new_records.append(record)
            _logger.info(f"new record xvx {new_headers} ===== {records}")
            
            if new_headers:
                return {
                    'headers': new_headers, #[list(records[0][r].keys()) for r in records[0]][0], 
                    'records': records,
                    'status': True,
                    'message': ''
                }
            else:
                return {
                    'headers': [],
                    'records': records,
                    'status': False,
                    'message': 'No header found to build MMR'
                }
            
        else:
            return {
                'headers': [],
                'records': records,
                'status': False,
                'message': 'No record found to build MMR'
            }
        _logger.info(f"Final value of records to display {records}")

    def line_doughnut_filter_project_type_data(self, domain, kwargs):
        '''docs: returns: project_x_data, budget_amount_project_y_data, revenue_amount_project_y_data
        [], [], []
        '''
        memo_obj = request.env['memo.model'].search(domain)
        budget_amount_project_y_data = []
        revenue_amount_project_y_data = []
        month_sales_project_x_data = []
        project_x_data = []
        project_element = []
        if memo_obj:
            project_items = list(set([mm.memo_type.memo_key for mm in memo_obj])) if kwargs.get('project_file_type') else list(set([mm.memo_project_type for mm in memo_obj]))
            project_dicts = {}
            for pupdate in project_items:
                project_dicts[f'{pupdate}'] = {
                    'revenue_total': 0, 
                    'budget_total': 0, 
                    'month_sales': None,
                    'usd_revenue_total': 0,
                    'usd_budget_total': 0,
                    }
            currency_name = kwargs.get('currency_name')
            for rec in memo_obj:
                mtype = rec.memo_project_type if not kwargs.get('project_file_type') else rec.memo_type.memo_key
                # mtype = rec.memo_type.memo_key
                rec_revenue_months = list(set([r.date_order.strftime('%b') for r in rec.mapped('so_ids').filtered(lambda so: so.state not in ['draft', 'cancel'])]))
                revenue_total, budget_total, usd_revenue_total, usd_budget_total = 0, 0, 0, 0
                budget_rev_total, invoice_revenue_total, invoice_paid_revenue = self.compute_so_naira_dollar_value(rec.so_ids, 'USD') if currency_name in ['USD'] else \
                    self.compute_so_naira_dollar_value(rec.so_ids, 'NGN')
        
                revenue_total = invoice_revenue_total 
                budget_total = budget_rev_total 
                revenue_project_total = project_dicts.get(f'{mtype}').get('revenue_total') + revenue_total
                budget_project_total = project_dicts.get(f'{mtype}').get('budget_total') + budget_total
                # usd_revenue_project_total = project_dicts.get(f'{mtype}').get('usd_revenue_total') + usd_revenue_total
                # usd_budget_project_total = project_dicts.get(f'{mtype}').get('usd_budget_total') + usd_budget_total
                project_dicts.get(f'{mtype}').update({
                    'revenue_total':revenue_project_total, 
                    'budget_total':budget_project_total,
                    'month_sales': rec_revenue_months,
                    # 'usd_revenue_project_total':usd_revenue_project_total,
                    # 'usd_budget_project_total':usd_budget_project_total,
                    'client_id': rec.client_id.name#  if 'customer_name' in kwargs else '',
                    })
                project_element.append(project_dicts)
            project_x_data = [r.capitalize().split('_')[0] for r in list(project_dicts.keys())]
            for k, v in project_dicts.items():
                revenue_amount_project_y_data.append(project_dicts.get(f'{k}').get('revenue_total'))
                budget_amount_project_y_data.append(project_dicts.get(f'{k}').get('budget_total'))
                month_sales_project_x_data.append(project_dicts.get(f'{k}').get('month_sales'))
            return project_x_data, budget_amount_project_y_data, revenue_amount_project_y_data, month_sales_project_x_data, project_element
        else:
            return project_x_data, budget_amount_project_y_data, revenue_amount_project_y_data,month_sales_project_x_data, project_element
      
    def get_sales_by_month(self, kwargs={}, memo_type_params=False):
        memo_type_params= [] if not memo_type_params else memo_type_params
        domain = [
            ('memo_id', '!=', False), 
            ('state', 'not in', ['draft', 'cancel']),
            ]
        sales = request.env['sale.order'].search(domain)
        items = {'Jan': {'total': 0}, 'Feb': {'total': 0}, 'Mar': {'total': 0}, 'Apr': {'total': 0}, 'May': {'total': 0}, 'Jun': {'total': 0}, 'Jul': {'total': 0}, 'Aug': {'total': 0}, 'Sep': {'total': 0}, 'Oct': {'total': 0}, 'Nov': {'total': 0}, 'Dec': {'total': 0}}
        currency_name = kwargs.get('currency_name')
        if sales:
            for so in sales:
                s_date = so.date_order.strftime('%b')
                budget_rev_total, invoice_revenue_total, invoice_paid_revenue = self.compute_so_naira_dollar_value(so, 'USD') if currency_name in ['USD'] else \
                    self.compute_so_naira_dollar_value(so, 'NGN')
                so_amount = invoice_revenue_total + invoice_paid_revenue
                amount = items.get(f'{s_date}').get('total') + so_amount
                items.get(f'{s_date}').update({'total': amount})
        sale_amount = [i.get('total') for i in items.values()]
        months = list(items.keys())
        return months, sale_amount
 
    # def compute_po_naira_dollar_value(self, poo, currency='NGN'):
    #     total_cost, total_invoiced_cost, total_paid_cost = 0, 0, 0
    #     if poo:
    #         _logger.info(f'TEST MY {poo}')
    #         for po in poo:
    #             currency_id = po.currency_id
    #             # compute btw dates of date approve
    #             two_date_before, two_date_after = po.date_approve or po.date_order + timedelta(days=-2), po.date_approve or po.date_order + timedelta(days=2)
    #             if currency in ['Naira', 'NGN']:
    #                 # do conversion to naira value
    #                 if currency_id.name == 'USD' or currency_id.id == 1:
    #                     # set the inverse company rate. ie compute from USD to naira
    #                     # filter the currency rate as at that time, if not found, used the current rate
    #                     # e.g 22 sep < 24 sep > 26 sept
    #                     currency_rate = currency_id.mapped('rate_ids').filtered(
    #                         lambda cr: two_date_before.date() < cr.name and two_date_after.date() > cr.name
    #                         )
    #                     currency_usd_id = request.env.ref('base.USD')
    #                     usd_rate = currency_usd_id.mapped('rate_ids')
                        
    #                     currency_rate_alternative = currency_id.rate_ids
    #                     if currency_rate.ids: # if currency_rate or usd_rate:
    #                         _logger.info(f"am joj {currency_rate}")
    #                         rate = currency_rate[0].inverse_company_rate# or currency_rate_alternative[0].inverse_inverse_company_rate
    #                         total_cost += po.amount_total * rate
    #                         total_invoiced_cost += po.amount_total * rate if po.state not in ['draft', 'cancel'] else 0
    #                         total_paid_cost += po.amount_total * rate if po.invoice_status in ['invoiced'] else 0
    #                         # ie. 50000 * 0.002600
    #                     elif usd_rate:
    #                         rate = usd_rate[0].inverse_company_rate
    #                         total_cost += po.amount_total * rate
    #                         total_invoiced_cost += (po.amount_total * rate) if po.state not in ['draft', 'cancel'] else 0
    #                         total_paid_cost += (po.amount_total * rate) if po.invoice_status in ['invoiced'] else 0
    #                     else:
    #                         raise ValidationError('You must ensure that both currencies (NGN, USD) has at least an update rate ids')
    #                 else: # value to display is in naira
    #                     total_cost += po.amount_total
    #                     total_invoiced_cost += po.amount_total if po.state not in ['draft', 'cancel'] else 0
    #                     total_paid_cost += po.amount_total if po.invoice_status in ['invoiced'] else 0
    #             else: 
    #                 # Convert all to USD value
    #                 if currency_id.name in ['NGN', 'Naira', False] or currency_id.currency_unit_label == 'Naira':
    #                     # set the company rate. ie compute from naira to USD
    #                     # filter the currency rate as at that time, if not found, used the current rate
    #                     # e.g 22 sep < 24 sep > 26 sept
    #                     currency_usd_id = request.env.ref('base.USD')
    #                     usd_rate = currency_usd_id.mapped('rate_ids')
                        
    #                     currency_rate = usd_rate.filtered(
    #                         lambda cr: two_date_before.date() < cr.name and two_date_after.date() > cr.name
    #                         )
    #                     # currency_rate_alternative = currency_id.rate_ids
    #                     if currency_rate.ids:
    #                         rate = currency_rate[0].inverse_company_rate or usd_rate[0].inverse_company_rate
    #                         # total += po.amount_total / rate
    #                         total_cost += float(po.amount_total / rate)
    #                         total_invoiced_cost += (po.amount_total / rate) if po.state not in ['draft', 'cancel'] else 0
    #                         total_paid_cost += po.amount_total / rate if po.invoice_status in ['invoiced'] else 0
                            
    #                         # ie. 50000 * 1600
    #                     elif usd_rate:
    #                         rate = usd_rate[0].inverse_company_rate
    #                         total_cost += float(po.amount_total / rate)
    #                         total_invoiced_cost += (po.amount_total / rate) if po.state not in ['draft', 'cancel'] else 0
    #                         total_paid_cost += (po.amount_total / rate) if po.invoice_status in ['invoiced'] else 0
                            
    #                     else:
    #                         raise ValidationError('You must ensure that both currencies (NGN, USD) has at least an update rate ids')
    #                 else: # value to display is in USD
    #                     total_cost += po.amount_total
    #                     total_invoiced_cost += po.amount_total if po.state not in ['draft', 'cancel'] else 0
    #                     total_paid_cost += po.amount_total if po.invoice_status in ['invoiced'] else 0
                    
    #     return round(total_cost), round(total_invoiced_cost), round(total_paid_cost)
    
    def compute_po_naira_dollar_value(self, po_ids, currency='NGN'):
        """po_ids: po_ids or po_id"""
        total_cost, total_invoiced_cost, total_paid_cost, total_po_to_be_invoiced = 0.00, 0.00, 0.00, 0.00
        if po_ids:
            _logger.info(f'TEST MY {po_ids}')
            for po in po_ids:
                currency_id = po.currency_id
                # compute btw dates of date approve
                two_date_before, two_date_after = po.date_approve or po.date_order + timedelta(days=-2), po.date_approve or po.date_order + timedelta(days=2)
                if currency in ['Naira', 'NGN']:
                    # do conversion to naira value
                    if currency_id.name == 'USD' or currency_id.id == 1:
                        # set the inverse company rate. ie compute from USD to naira
                        # filter the currency rate as at that time, if not found, used the current rate
                        # e.g 22 sep < 24 sep > 26 sept
                        currency_rate = currency_id.mapped('rate_ids').filtered(
                            lambda cr: two_date_before.date() < cr.name and two_date_after.date() > cr.name
                            )
                        currency_usd_id = request.env.ref('base.USD')
                        usd_rate = currency_usd_id.mapped('rate_ids')
                        
                        currency_rate_alternative = currency_id.rate_ids
                        if currency_rate.ids: # if currency_rate or usd_rate:
                            rate = currency_rate[0].inverse_company_rate# or currency_rate_alternative[0].inverse_inverse_company_rate
                            total_cost += po.amount_total * rate
                            total_invoiced_cost += po.amount_total * rate if po.state not in ['draft', 'cancel'] else 0.00
                            total_paid_cost += po.amount_total * rate if po.invoice_status in ['invoiced'] else 0.00
                            total_po_to_be_invoiced += float(po.amount_total * rate) if po.invoice_status not in ['invoiced'] else 0.00
                            _logger.info(f"Naira filter with USD @ rate: {currency_rate} == {total_invoiced_cost} ")
                            # ie. 50000 * 0.002600
                        else:
                            # usd_rate:
                            rate = usd_rate[0].inverse_company_rate
                            total_cost += po.amount_total * rate
                            total_invoiced_cost += (po.amount_total * rate) if po.state not in ['draft', 'cancel'] else 0.00
                            total_paid_cost += (po.amount_total * rate) if po.invoice_status in ['invoiced'] else 0.00
                            total_po_to_be_invoiced += float(po.amount_total * rate) if po.invoice_status not in ['invoiced'] else 0.00
                            _logger.info(f"Naira filter with default USD Amount {po.amount_total} converted @ rate {rate} === {total_invoiced_cost}")
                        # else:
                        #     raise ValidationError('You must ensure that both currencies (NGN, USD) has at least an update rate ids')
                    else: # value to display is in naira
                        total_cost += po.amount_total
                        total_invoiced_cost += po.amount_total if po.state not in ['draft', 'cancel'] else 0.00
                        total_paid_cost += po.amount_total if po.invoice_status in ['invoiced'] else 0.00
                        total_po_to_be_invoiced += float(po.amount_total) if po.invoice_status not in ['invoiced'] else 0.00
                else: 
                    # Convert all to USD value
                    if currency_id.name in ['NGN', 'Naira', False] or currency_id.currency_unit_label == 'Naira':
                        # set the company rate. ie compute from naira to USD
                        # filter the currency rate as at that time, if not found, used the current rate
                        # e.g 22 sep < 24 sep > 26 sept
                        currency_usd_id = request.env.ref('base.USD')
                        usd_rate = currency_usd_id.mapped('rate_ids')
                        currency_rate = usd_rate.filtered(
                            lambda cr: two_date_before.date() < cr.name and two_date_after.date() > cr.name
                            )
                        # currency_rate_alternative = currency_id.rate_ids
                        if currency_rate.ids:
                            rate = currency_rate[0].inverse_company_rate or usd_rate[0].inverse_company_rate
                            # total += po.amount_total / rate
                            total_cost += float(po.amount_total / rate)
                            total_invoiced_cost += (po.amount_total / rate) if po.state not in ['draft', 'cancel'] else 0.00
                            total_paid_cost += po.amount_total / rate if po.invoice_status in ['invoiced'] else 0.00
                            total_po_to_be_invoiced += float(po.amount_total / rate) if po.invoice_status not in ['invoiced'] else 0.00
                            # ie. 50000 * 1600
                        elif usd_rate:
                            rate = usd_rate[0].inverse_company_rate
                            total_cost += float(po.amount_total / rate)
                            total_invoiced_cost += (po.amount_total / rate) if po.state not in ['draft', 'cancel'] else 0.00
                            total_paid_cost += (po.amount_total / rate) if po.invoice_status in ['invoiced'] else 0.00
                            total_po_to_be_invoiced += float(po.amount_total / rate) if po.invoice_status not in ['invoiced'] else 0.00
                        else:
                            raise ValidationError('You must ensure that both currencies (NGN, USD) has at least an update rate ids')
                    else: # value to display is in USD
                        total_cost += po.amount_total
                        total_invoiced_cost += po.amount_total if po.state not in ['draft', 'cancel'] else 0.00
                        total_paid_cost += po.amount_total if po.invoice_status in ['invoiced'] else 0.00
                        total_po_to_be_invoiced += float(po.amount_total) if po.invoice_status not in ['invoiced'] else 0.00
        return round(total_cost), round(total_invoiced_cost), round(total_paid_cost), round(total_po_to_be_invoiced, 2)
    
    def compute_so_naira_dollar_value(self, so_ids, currency='NGN'):
        total_budget_revenue, total_invoiced_revenue, total_paid_revenue = 0, 0, 0
        if so_ids:
            currency_usd_id = request.env.ref('base.USD') 
            usd_rate = currency_usd_id.mapped('rate_ids')
            rate = usd_rate[0].inverse_company_rate
            for so in so_ids:
                currency_id = so.pricelist_id.currency_id
                # compute btw dates of date approve
                two_date_before, two_date_after = so.date_order + timedelta(days=-2), so.date_order + timedelta(days=2)
                if currency in ['Naira', 'NGN']:
                    # do conversion to naira value
                    if currency_id.name == 'USD' or currency_id.id == 1:
                        # set the inverse company rate. ie compute from USD to naira
                        # filter the currency rate as at that time, if not found, used the current rate
                        # e.g 22 sep < 24 sep > 26 sept
                        currency_rate = currency_id.mapped('rate_ids').filtered(
                            lambda cr: two_date_before.date() < cr.name and two_date_after.date() > cr.name
                            )
                        currency_rate_alternative = currency_id.rate_ids
                        if currency_rate.ids: # or currency_rate_alternative:
                            # rate = currency_rate[0].inverse_inverse_company_rate# or currency_rate_alternative[0].inverse_inverse_company_rate
                            rate = currency_rate[0].inverse_company_rate# or currency_rate_alternative[0].inverse_inverse_company_rate
                            total_budget_revenue += float(so.amount_total * rate)
                            total_invoiced_revenue += float(so.amount_total * rate) if so.state not in ['draft', 'cancel'] else 0
                            total_paid_revenue += float(so.amount_total * rate) if so.invoice_status in ['invoiced'] else 0
                            # ie. 50000 * 0.002600
                        elif usd_rate:
                            rate = usd_rate[0].inverse_company_rate
                            total_budget_revenue += float(so.amount_total * rate)
                            total_invoiced_revenue += float(so.amount_total * rate) if so.state not in ['draft', 'cancel'] else 0
                            total_paid_revenue += float(so.amount_total * rate) if so.invoice_status in ['invoiced'] else 0
                        else:
                            raise ValidationError('You must ensure that both currencies (NGN, USD) has at least an update rate ids')
                    else: # value to display is in naira
                        total_budget_revenue += float(so.amount_total)
                        total_invoiced_revenue += float(so.amount_total) if so.state not in ['draft', 'cancel'] else 0
                        total_paid_revenue += float(so.amount_total) if so.invoice_status in ['invoiced'] else 0
                else: 
                    # Convert all value to USD value
                    # _logger.info(f'Rate SO converted {so.amount_total} --- {so.amount_total / 1600}')
                    # _logger.info(f"AT WHAT RATE 2{so.name}")
                    # total_budget_revenue += float(so.amount_total / rate)
                    # total_invoiced_revenue += float(so.amount_total / rate) if so.state not in ['draft', 'cancel'] else 0
                    # total_paid_revenue += float(so.amount_total / rate) if so.invoice_status in ['invoiced'] else 0
                    # _logger.info(f"AT WHAT RATE 12  {total_invoiced_revenue}")
                    if currency_id.name in ['NGN', 'Naira', False]:# or currency_id.currency_unit_label == 'Naira':
                        currency_rate = usd_rate.filtered(
                            lambda cr: two_date_before.date() < cr.name and two_date_after.date() > cr.name)
                        if currency_rate.ids:
                            # _logger.info(f'Rate sxxxx SO {currency_usd_id} --- {so}... {currency_rate} or {usd_rate}')
                            rate = currency_rate[0].inverse_company_rate or usd_rate[0].inverse_company_rate
                            # total += so.amount_total / rate
                            total_budget_revenue += float(so.amount_total / rate)
                            total_invoiced_revenue += float(so.amount_total / rate) if so.state not in ['draft', 'cancel'] else 0
                            total_paid_revenue += float(so.amount_total / rate) if so.invoice_status in ['invoiced'] else 0
                            # ie. 50000 * 1600
                        # elif usd_rate:
                        else: # usd_rate:
                            
                            rate = usd_rate[0].inverse_company_rate
                            # total += so.amount_total / rate
                            total_budget_revenue += float(so.amount_total / rate)
                            total_invoiced_revenue += float(so.amount_total / rate) if so.state not in ['draft', 'cancel'] else 0
                            _logger.info(f"CONVERSI {so.amount_total} AND {rate} === {so.amount_total / rate}")
                            total_paid_revenue += float(so.amount_total / rate) if so.invoice_status in ['invoiced'] else 0
                            _logger.info(f"AT WHAT RATE {so.id} ===> {so.amount_total} RATE: {rate} TOTAL {total_invoiced_revenue}")
                            _logger.info(f"Naira SO filter with USD @ rate: {rate} == {total_invoiced_revenue} ")
                        # else:
                        #     raise ValidationError('You must ensure that currencies (USD) has at least an update rate ids')
                    else: # value to display is in USD
                        _logger.info(f"AT WHAT RATE 2{so.name}")
                        # total += so.amount_total
                        total_budget_revenue += float(so.amount_total)
                        total_invoiced_revenue += float(so.amount_total) if so.state not in ['draft', 'cancel'] else 0
                        total_paid_revenue += float(so.amount_total) if so.invoice_status in ['invoiced'] else 0
        return round(total_budget_revenue, 3), round(total_invoiced_revenue, 3), round(total_paid_revenue, 3)
    
    def line_doughnut_filter_customer_data(self, domain, kwargs={}):
        '''docs: 
        returns: customer_x_data, budget_amount_customer_y_data, revenue_amount_customer_y_data [], [], []
        '''
        project_x_data = []
        budget_amount_project_y_data = []
        revenue_amount_project_y_data = []
        memo_obj = request.env['memo.model'].search(domain)
        customer_project_items_name= []
        customer_project_items = []
        budget_amount_project_y_data = []
        revenue_amount_project_y_data = []
        usd_budget_amount_project_y_data = []
        usd_revenue_amount_project_y_data = []
        customer_project_dicts = {}
        currency_name = kwargs.get('currency_name')
        
        if memo_obj:
            customer_project_items = list(set([mm.client_id.id for mm in memo_obj]))
            customer_project_items_name = list(set([mm.client_id.name for mm in memo_obj]))
            for cupdate in customer_project_items:
                customer_project_dicts[f'{cupdate}'] = {
                    'name': request.env['res.partner'].browse([cupdate]).name, 
                    'revenue_total': 0, 
                    'budget_total': 0,
                    'usd_revenue_total': 0,
                    'usd_budget_total': 0,
                    }
            # e.g {'travel': {'revenue_total': 34400, 'budget_total': 6000}, 'logistics': {'total': 34400}}
            for rec in memo_obj: 
                budget_total, revenue_total, usd_revenue_total, usd_budget_total = 0,0,0,0 
                computed_invoice_result = self.compute_so_naira_dollar_value(rec.so_ids, 'USD') if currency_name in ['USD'] else \
                    self.compute_so_naira_dollar_value(rec.so_ids, 'NGN')
                budget_total, revenue_total, paid_revenue_total = computed_invoice_result, 
                budget_project_total = customer_project_dicts.get(f'{rec.client_id.id}').get('budget_total') + budget_total
                revenue_project_total = customer_project_dicts.get(f'{rec.client_id.id}').get('revenue_total') + revenue_total
                
                usd_revenue_project_total = customer_project_dicts.get(f'{rec.client_id.id}').get('usd_revenue_total') + usd_revenue_total
                usd_budget_project_total = customer_project_dicts.get(f'{rec.client_id.id}').get('usd_budget_total') + usd_budget_total
                customer_project_dicts.get(f'{rec.client_id.id}').update({
                    'budget_total':budget_project_total,
                    'revenue_total':revenue_project_total, 
                    'usd_revenue_project_total':usd_revenue_project_total,
                    'usd_budget_project_total':usd_budget_project_total,
                    })
            for k, v in customer_project_dicts.items():
                revenue_amount_project_y_data.append(customer_project_dicts.get(f'{k}').get('revenue_total'))
                budget_amount_project_y_data.append(customer_project_dicts.get(f'{k}').get('budget_total'))
                usd_revenue_amount_project_y_data.append(customer_project_dicts.get(f'{k}').get('usd_revenue_project_total'))
                usd_budget_amount_project_y_data.append(customer_project_dicts.get(f'{k}').get('usd_budget_project_total'))
        return customer_project_items_name, budget_amount_project_y_data, revenue_amount_project_y_data, \
            usd_revenue_amount_project_y_data,usd_budget_amount_project_y_data, customer_project_dicts
    
    def get_clients_to_pay(self):
        return ['a', 'b', 'c', 'r']

    def get_xy_data(self, memo_type_param="document_request"):
        '''Test for document charts
        1. configure document folder with occurrence and min and max range set to 2 . ie two days
        2. Create a new memo of type document request,
        3. Approve the memo, 
        4. Reset the next occurrence and try again
        '''
        department_total_progress, items = [30, 45, 60, 75, 68, 78, 88, 100], ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        return department_total_progress, items
        # [hr_department.browse(dp).name for dp in list(set(departments))]

    @http.route(["/memo-records"], type='http', auth='user', website=True, website_published=True)
    def open_related_record_view(self):
        url = "/web#action=487&model=memo.model&view_type=list&cids=1&menu_id=333"
        return request.redirect(url)

    @http.route(['/display-mmr-data'], type='json', website=True, auth="user", csrf=False)
    def display_MMR(self, **post):
        kwargs = dict(
            project_file_type = post.get('project_file_type'),
            memo_project_type = post.get('memo_project_type'),
            customer_id = post.get('customer_id'),
            code = post.get('code'),
            date_from = post.get('date_from'),
            date_to = post.get('date_to'),
            currency_name = post.get('currency_name'),
            year = post.get('year'),
            month = post.get('month'),
            branch = post.get('branch'),
            )
        
        memo_type_ids = ['warehouse', 'procurement', 'agency', 'cfwd', 'transport', 'travel']
        memo_project_type_ids = [kwargs.get('memo_project_type')] if kwargs.get('memo_project_type') else memo_type_ids
        # first domain with current year
        current_year = datetime.now().year
        subsequent_year = datetime.now().year + 1
        cy = datetime.strptime(f"01/01/{current_year}", "%m/%d/%Y")
        scy = datetime.strptime(f"01/01/{current_year}", "%m/%d/%Y")

        domain = [
            ('active', '=', True), 
            ('memo_project_type', 'in', memo_project_type_ids),
            # ('create_date', '>', '2024-12-30'),
            # ('closing_date', '<', scy.date())
            # ('closing_date', '>=', f'{current_year}-01-01'),
            # ('closing_date', '<', f'{current_year + 1}-01-01')
            ]
        

        if kwargs.get('customer_id'): # if client is selected
            domain = domain + [('client_id', '=', int(kwargs.get('customer_id')))]
        if kwargs.get('month') or kwargs.get('year'):
            # by default , show the MMR for the current year and later check if year or month is added to domain
            month_domain = self.get_memo_with_month_year(kwargs.get('month'), kwargs.get('year'))
            domain += month_domain #
        _logger.info(f"show me domain {domain}")
        vals=self.dynamic_mmr_table(domain, kwargs)
        return vals
    
    @http.route(['/display-file-admin'], type='json', website=True, auth="user", csrf=False)
    def displayFileAdmin(self, **post):
        kwargs = dict(
            project_file_type = post.get('project_file_type'),
            customer_name = post.get('customer_name'),
            code = post.get('code'),
            date_from = post.get('date_from'),
            date_to = post.get('date_to'),
            currency_name = post.get('currency_name'),
            frame_agreement_id = post.get('frame_agreement_id'),
            year = post.get('year'),
            month = post.get('month'),
            branch = post.get('branch'),
            )
        currency_name = kwargs.get('currency_name')
        domain = [('active', '=', True), ('memo_project_type', 'in', ['warehouse', 'procurement', 'agency', 'cfwd', 'transport', 'travel'])] 
        if kwargs.get('project_file_type'):
            project_file_type = [int(kwargs.get('project_file_type'))]
            domain += [('memo_type', 'in', project_file_type)]
            
        if kwargs.get('customer_name'):
            customer_ids = [int(kwargs.get('customer_name'))]
            domain += [('client_id', 'in', customer_ids)]
        if kwargs.get('frame_agreement_id'):
            fr_id = int(kwargs.get('frame_agreement_id'))
            fr_domain = self.get_memo_with_frame_agreement(fr_id)
            if fr_domain:
                domain = domain + fr_domain 
        _logger.info(f'This ko kwargs {kwargs} and {domain}')
        
        memo_ids = request.env["memo.model"].sudo().search(domain)
        _logger.info(f'This is fer 0 {memo_ids}')
        
        # Getting the month and year filters
        month, year = kwargs.get('month'), kwargs.get('year')
        if month and not year:
            memo_ids = memo_ids.filtered(lambda mon: mon.date.strftime('%b') == month)
        if year and not month:
            memo_ids = memo_ids.filtered(lambda mon: mon.date.strftime('%Y') == year)
        if year and month:
            memo_ids = memo_ids.filtered(lambda mon: mon.date.strftime('%b') == month and mon.date.strftime('%Y') == year)
        #####################################3 
        vals=self.dynamicFileAdmin(memo_ids)
        _logger.info(f'This is fer {vals} and {memo_ids}')
        return vals
    
    def dynamicFileAdmin(self, memo_ids):
        output_opened_files, closed_file_ids = [], []
        to_be_invoiced_ids = []
        past_one_week_ids, past_two_week_ids, past_one_month_ids = [], [], []
        
        files_to_be_closeds = []
        files_to_be_approveds = []
        so_payment_not_registereds = []
        pos_to_be_approved_ids = []
        files_wto_cost = []
        files_wto_rev = []
        closed_file_ids = [] 
        # invoices_to_be_validateds = []
        pos_to_be_paid_ids = []
        today_date = fields.Date.today()
        if memo_ids:
            for mo in memo_ids: 
                ########## computing the long overdue files 
                last_stage_id = self.get_memo_last_stage(mo)
                if mo.stage_id.id == last_stage_id[-2].id: 
                    files_to_be_closeds.append(mo.id)
                    
                if mo.stage_id.id == last_stage_id[-1].id: # determine if the file is at closed stage
                    closed_file_ids.append(mo.id)
                else:
                    output_opened_files.append(mo.id) # determine if the file is not at closed stage
                    #################### computing overdue files
                    date_difference = today_date - mo.date.date()
                    if date_difference.days in range (0, 7):
                        past_one_week_ids.append(mo.id)
                    elif date_difference.days in range (8, 30):
                        past_two_week_ids.append(mo.id)
                        
                    elif date_difference.days >= 30:
                        past_one_month_ids.append(mo.id)
                    
                    if mo.state not in ['submit','refuse']:
                        if mo.po_ids and not mo.so_ids:
                            to_be_invoiced_ids.append(mo.id)
                        if not mo.po_ids:
                            # files not with po_ids
                            files_wto_cost.append(mo.id)
                        if not mo.so_ids:
                            # files not with so_ids
                            files_wto_rev.append(mo)
                    
                    if mo.state in ['Sent']: # to be approved
                        files_to_be_approveds.append(mo.id)
                        
                    if mo.mapped('so_ids').filtered(lambda s: s.invoice_status not in ['invoiced']):
                        # if any sale order payment not registered in accounts
                        so_payment_not_registereds.append(mo.id)
                 
                    if mo.mapped('po_ids').filtered(lambda s: s.invoice_status not in ['invoiced']):
                        # if any sale order payment not registered in accounts
                        pos_to_be_paid_ids.append(mo.id)
                        
                    if mo.mapped('po_ids').filtered(lambda s: s.state in ['draft']):
                        # if any sale order payment not registered in accounts
                        pos_to_be_approved_ids.append(mo.id)
                        
        return{ 
            "output_opened_files": {'count': len(output_opened_files), 'records': str(output_opened_files)},
            "closed_file_ids": {'count': len(closed_file_ids), 'records': str(closed_file_ids)},
            "past_one_week_ids": {'count': len(past_one_week_ids), 'records': str(past_one_week_ids)},
            "past_two_week_ids": {'count': len(past_two_week_ids), 'records': str(past_two_week_ids)},
            "past_one_month_ids": {'count': len(past_one_month_ids), 'records': str(past_one_month_ids)},
            "files_to_be_closeds": {'count': len(files_to_be_closeds), 'records': str(files_to_be_closeds)},
            "files_to_be_approveds": {'count': len(files_to_be_approveds), 'records': str(files_to_be_approveds)},
            "so_payment_not_registereds": {'count': len(so_payment_not_registereds), 'records': str(so_payment_not_registereds)},
            "pos_to_be_approved_ids": {'count': len(pos_to_be_approved_ids), 'records': str(pos_to_be_approved_ids)},
            "files_wto_cost": {'count': len(files_wto_cost), 'records': str(files_wto_cost)},
            "files_wto_rev": {'count': len(files_wto_rev), 'records': str(files_wto_rev)},
            "pos_to_be_paid_ids": {'count': len(pos_to_be_paid_ids), 'records': str(pos_to_be_paid_ids)},
            "company_name": request.env.user.company_id.name
            }            
          
    
    @http.route(['/display-frame-agreeement'], type='json', website=True, auth="user", csrf=False)
    def displayFrame_agreement(self, **post):
        kwargs = dict(
            project_file_type = post.get('project_file_type'),
            customer_name = post.get('customer_name'),
            code = post.get('code'),
            date_from = post.get('date_from'),
            date_to = post.get('date_to'),
            currency_name = post.get('currency_name'),
            frame_agreement_id = post.get('frame_agreement_id'),
            year = post.get('year'),
            month = post.get('month'),
            branch = post.get('branch'),
            )
        # domain=[('active', '=', True)]
        domain = [('active', '=', True), ('memo_project_type', 'in', ['warehouse', 'procurement', 'agency', 'cfwd', 'transport', 'travel'])] 
        vals=self.dynamic_frame_agreement(domain, kwargs)
        return vals
    
    def dynamic_frame_agreement(self, domain, kwargs={}):
        """
        This compute the sum of all agreement on the memos of client and displays the confirmed invoices amount and 
        compares it with the total max agreed budget for that project
        e.g if the total agreed max budget (frame_agreement_ids) is 500,000 and total confirmed invoices is 100,000
        system computes the percentage ratio as 100,000 * 100 / 500,000 = 20 %
        The green shows 20 % while the budget (red ) shows 80 %
        """
        currency_usd_id = request.env.ref('base.USD') 
        usd_rate = currency_usd_id.mapped('rate_ids')
        rate = usd_rate[0].inverse_company_rate
        frame_agreement = request.env['memo.frame.agreement']
        memo = request.env['memo.model']
        fr_id = None
        
        if kwargs.get('project_file_type'):
            project_file_type = [int(kwargs.get('project_file_type'))]
            domain += [('memo_type', 'in', project_file_type)]
            
        if kwargs.get('customer_name'):
            customer_ids = [int(kwargs.get('customer_name'))]
            domain += [('client_id', 'in', customer_ids)]
        domain = domain + [('frame_agreement_ids', '!=', False)]
        if kwargs.get('frame_agreement_id'):
            fr_id = int(kwargs.get('frame_agreement_id'))
            fr_domain = self.get_memo_with_frame_agreement(fr_id)
            if fr_domain:
                domain = domain + fr_domain 
        _logger.info(f"WHat is domain new {domain}")
        frame_memo_ids = memo.search(domain)
        
        # Getting the month and year filter
        month, year = kwargs.get('month'), kwargs.get('year')
        if month and not year:
            frame_memo_ids = frame_memo_ids.filtered(lambda mon: mon.date.strftime('%b') == month)
        if year and not month:
            frame_memo_ids = frame_memo_ids.filtered(lambda mon: mon.date.strftime('%Y') == year)
        if year and month:
            frame_memo_ids = frame_memo_ids.filtered(lambda mon: mon.date.strftime('%b') == month and mon.date.strftime('%Y') == year)
        #####################################3
        
        _logger.info(f"the new memos agreement {frame_memo_ids}")
        
        currency_name = kwargs.get('currency_name')
        frame_agreement_budget, confirmed_so, all_so, balance = 0,0,0,0
        if frame_memo_ids:
            for x in frame_memo_ids:
                for fr in x.frame_agreement_ids: # you can filter the only frame id as x.mapped(frame_agreement_ids).filtered(lambda f: f.fr_id)
                    frame_agreement_budget += fr.agreed_budget
                
                # confirmed_so_ids = x.mapped('so_ids').filtered(lambda s: s.state not in ['cancel', 'draft'])
                # all_so_ids = x.mapped('so_ids').filtered(lambda s: s.state not in ['cancel'])
                
                budget_revenue_total, invoice_revenue_total, invoice_paid_revenue = self.compute_so_naira_dollar_value(x.so_ids, 'USD') if currency_name in ['USD'] else \
                    self.compute_so_naira_dollar_value(x.so_ids, 'NGN')
                amt = invoice_revenue_total + invoice_paid_revenue
                confirmed_so += amt
                all_so += budget_revenue_total
        balance = frame_agreement_budget - confirmed_so
        frame_agreement_budget = frame_agreement_budget if frame_agreement_budget > 0 else 1
        frame_agreement_budget = frame_agreement_budget / rate if currency_name in ['USD'] else frame_agreement_budget #/ rate
        # invoices_ratio = (confirmed_so * 120) / frame_agreement_budget # e.g (10000 * 100) / 20000 = 50 %
        invoices_ratio = (confirmed_so / frame_agreement_budget) * 120 # e.g (10000 * 100) / 20000 = 50 %
        fr_budget_ratio = 120 - invoices_ratio
        
        invoices_ratio = 120 if invoices_ratio > 120 else 0 if invoices_ratio < 0 else invoices_ratio
        fr_budget_ratio = 120 if fr_budget_ratio > 120 else 0 if fr_budget_ratio < 0 else fr_budget_ratio
        # frame agreement ratio
        return {
            'frame_agreement_x': ['All Invoices', 'Danger Zone', 'Frame Budget'], #, 'Paid Invoice', 'Balance'], 
            'frame_agreement_y': [80, 20, 20], # [round(invoices_ratio), round(fr_budget_ratio)], #, all_so, confirmed_so, balance], 
            'frame_agreement_fill': [round(invoices_ratio), round(fr_budget_ratio)],
            'confirmed_so': confirmed_so, 
            'all_so': all_so,
            'currency_symbol': '$' if currency_name in ['USD'] else '₦',
            'frame_agreement_budget': frame_agreement_budget,
            'frameNeedleValue': round(float(invoices_ratio)),
        }
        
        
    @http.route(['/refresh-data'], type='json', website=True, auth="user", csrf=False)
    def refresh_data(self, **post):
        kwargs = dict(
            project_file_type = post.get('project_file_type'),
            project_file_category_type = post.get('project_file_category_type'),
            customer_name = post.get('customer_name'),
            currency_name = post.get('currency_name'),
            code = post.get('code'),
            date_from = post.get('date_from'),
            date_to = post.get('date_to'),
            frame_agreement_id = post.get('frame_agreement_id'),
            year = post.get('year'),
            month = post.get('month'),
            branch = post.get('branch'),
            )
        vals = self.office_dashboard(kwargs=kwargs)
        return vals
        