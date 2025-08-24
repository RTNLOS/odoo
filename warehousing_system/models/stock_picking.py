from odoo import api, fields, models, _
from datetime import date, timedelta
import logging
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
import re

_logger = logging.getLogger(__name__)

class MemoModel(models.Model):
    _inherit = 'memo.model'
    
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            if self.env.context.get('show_code_in_name'):
                name = record.code or ''
                record.display_name = name
            else:
                record.display_name = record.name

    def _search_display_name(self, operator, value):
        return ['|', ('name', operator, value), ('code', operator, value)]

class WarehouseInventory(models.Model):
    _inherit = 'stock.picking'
    _order = "id desc"
    
    @api.model
    def create(self, vals):
        vals['is_saved'] = True
        result = super(WarehouseInventory, self).create(vals)
        return result

    # NEW FIELDS AS PER REQUIREMENTS
    period_date_filter = fields.Date(
        string="Period Date Filter",
        help="Calendar view to choose date which will have effect on the days in storage"
    )
    
    days_multi = fields.Float(
        string="Days Multi",
        compute="_compute_days_multi",
        store=True,
        help="Multiplies modified date (as per date filtered) × Chargeable area"
    )
    
    total_area_new = fields.Float(
        string="New Total Area (m²)",
        compute="_compute_total_area_new", 
        store=True,
        help="New Total Area calculation = area per line item × quantity stored"
    )
    
    new_chargeable_area = fields.Float(
        string="New Chargeable Area (m²)",
        compute="_compute_new_chargeable_area",
        store=True,
        help="Sum of all Area M² in the shipment landing area"
    )
    
    dispatch_date_display = fields.Date(
        string="Dispatch Date",
        help="Literally pull dispatch date out to the list"
    )

    # NEW COMPUTED METHODS
    @api.depends('period_date_filter', 'area_chargeable', 'days_in_warehouse')
    def _compute_days_multi(self):
        for record in self:
            if record.period_date_filter and record.area_chargeable:
                days_diff = (fields.Date.today() - record.period_date_filter).days
                record.days_multi = days_diff * record.area_chargeable
            elif record.days_in_warehouse and record.area_chargeable:
                record.days_multi = record.days_in_warehouse * record.area_chargeable
            else:
                record.days_multi = 0.0

    @api.depends('move_ids_without_package', 'move_ids_without_package.area_m2', 'move_ids_without_package.product_uom_qty')
    def _compute_total_area_new(self):
        for record in self:
            total_area = 0.0
            for move in record.move_ids_without_package:
                line_total_area = move.area_m2 * move.product_uom_qty
                total_area += line_total_area
            record.total_area_new = total_area

    @api.depends('move_ids_without_package', 'move_ids_without_package.area_m2')
    def _compute_new_chargeable_area(self):
        for record in self:
            total_area = 0.0
            for move in record.move_ids_without_package:
                total_area += move.area_m2
            record.new_chargeable_area = total_area

    is_saved = fields.Boolean(default=False)
    
class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def action_resequence(self):
        """
        Finds the highest sequence number used for pickings of this type
        and sets the sequence to continue from that number.
        """
        self.ensure_one()
        if not self.sequence_id:
            raise UserError(_("This operation type does not have a dedicated sequence."))

        self.env.cr.execute("""
            SELECT name FROM stock_picking
            WHERE picking_type_id = %s AND name IS NOT NULL
            ORDER BY id DESC
            LIMIT 2000
        """, (self.id,))
        
        matches = [re.search(r'(\d+)$', rec[0]) for rec in self.env.cr.fetchall()]
        numbers = [int(m.group(1)) for m in matches if m]

        if not numbers:
            raise UserError(_("No existing records with a number suffix found to resequence from."))

        max_number = max(numbers)
        self.sequence_id.sudo().number_next_actual = max_number + 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Sequence Updated"),
                'message': _("The next number for this operation has been set to %s.", max_number + 1),
                'type': 'success',
                'sticky': False,
            }
        }

class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    _order = "id desc"
    
    def create_returns(self):
        picking_id = self.picking_id
        
        res = super(StockReturnPicking, self).create_returns()
        picking_id.inventory_status = 'draft'
        picking_id.state = 'draft'
        picking_id.is_saved = True
        for r in picking_id.move_ids:
            r.state = "draft"
        for r in picking_id.move_ids_without_package:
            r.state = "draft"
        return res


        