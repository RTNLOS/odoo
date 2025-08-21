from odoo import models, fields, _
from odoo.exceptions import UserError
import re

# class StockPicking(models.Model):
#     _inherit = 'stock.picking'

#     inventory_memo_id = fields.Many2one(
#         'memo.model',
#         string="Warehouse Inventory Memo",
#         help="When you receive goods, link them back to the warehouse‐inventory record."
#     )

#     receiving_waybill_number = fields.Char(string="Waybill Number (RL/AWB)")
#     # waybill_number    = fields.Char(string="Waybill Number (RL/AWB)")
#     bl_awb_number     = fields.Char(string="BL / AWB Number")
#     arrived_goods_img = fields.Binary(string="Image of Arrived Goods")
    
    
    
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