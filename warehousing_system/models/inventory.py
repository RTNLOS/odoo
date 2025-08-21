from odoo import api, fields, models
from datetime import date, timedelta
import logging
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

class MemoModel(models.Model):
    _inherit = 'memo.model'
    
    @api.depends('name', 'code')
    def _compute_display_name(self):
        """
        This method computes the display_name for memo records.
        It checks the context to decide which format to use.
        """
        for record in self:
            if self.env.context.get('show_code_in_name'):
                name = record.code or ''
                # if record.name and record.code != record.name:
                #      name = f"{record.code} / {record.name}"
                record.display_name = name
            else:
                record.display_name = record.name

    def _search_display_name(self, operator, value):
        """
        This method tells Odoo how to search on our computed field.
        It will search in both the 'name' and 'code' fields.
        """
        return ['|', ('name', operator, value), ('code', operator, value)]


class WarehouseInventory(models.Model):
    _inherit = 'stock.picking'
    _order = "id desc"
    
    
    @api.model
    def create(self, vals):
        vals['is_saved'] = True
        result = super(WarehouseInventory, self).create(vals)
        
        return result
    is_saved = fields.Boolean(default=False)
    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        picking_code = self.env.context.get('default_picking_type_code') or self.picking_type_code
        if self.warehouse_id:
            warehouse_picking_types = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', picking_code),
                ])
            self.update({
                'dummy_picking_type_ids': [(6, 0, warehouse_picking_types.ids)]
                })
        else:
            self.update({
                'dummy_picking_type_ids': False
                })
    active = fields.Boolean(default=True)
    def button_deactivate(self):
        if self.inventory_status == 'done':
            raise ValidationError("You cannot deactivate when the state is done")
        for rec in self.move_ids_without_package:
            rec.active = False
        self.active = False
        
    def button_activate(self):
        if self.active == False:
            self.active = True
            for rec in self.move_ids_without_package:
                rec.active = True
                    
    dummy_picking_type_ids = fields.Many2many(
        'stock.picking.type',
        string="Dummy Stock Picking type",
    )
     
    financial_id = fields.Many2one(
        'memo.model',
        string="Financial File",
        copy=True,
        help="Refers to the Purchase Order associated with this inventory receipt.",
        # domain=[('memo_type.memo_key','in', ['transport', 'warehouse'])]
        domain=[('state','not in', ['Done', 'Refuse'])],
        context={'show_code_in_name': True}
    )
    related_inbound_shipment = fields.Many2one(
        'stock.picking',
        string="Related Inbound Shipment",
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse",
        copy=True,
        help="Select the warehouse where the goods arrived or are expected."
    )
    inventory_status = fields.Selection(selection=[
        ('draft', "Draft"),
        ('arrived', "Allocated"),
        ('allocated', "Put Away"),
        ('done', 'Stored'),
        ('awaiting_dispatch', 'Awaiting Dispatch'),
        ('dispatch', 'Dispatched'),
        ('cancelled', 'Cancelled')
    ], string="Inventory Status",copy=True, default='draft', index=True, tracking=True)
    actual_date_of_arrival = fields.Date(
        string="Actual Arrival Date",
        tracking=True,
        copy=False,
        store=True
    )
    days_in_warehouse = fields.Integer(
        copy=False,
        string="Days in Storage (days)",
        compute="compute_days_in_storage"
    )

    @api.depends('actual_date_of_arrival')
    def compute_days_in_storage(self):
        for rec in self:
            if rec.actual_date_of_arrival:
                today = fields.Date.today()
                date_of_arrival = rec.actual_date_of_arrival
                diff = today - date_of_arrival
                rec.days_in_warehouse= diff.days
            else:
                rec.days_in_warehouse= 0

    receiving_supplier_id = fields.Many2one(
        'res.partner',
        string="Delivering Supplier/Vendor",
        # domain=[('supplier_rank', '>', 0)],
        help="The supplier who delivered the goods."
    )
    supplier_po_number = fields.Char(
        string="PO No.",
        copy=True,
        help="PO number from the supplier's system, if different from Odoo's PO."
    )
    dispatch_company = fields.Char(
        string="Dispatch company",
        copy=True,
    )
    transport_details = fields.Char(
        string="Transport Detail",
    )
    receiving_waybill_number = fields.Char(
        string="Waybill No. (RL/AWB)",
        copy=True,
        help="Receiving Log / Air Waybill number associated with the delivery."
    )
    bl_awb_number = fields.Char(string="BL/AWB No.", copy=True)
    expected_arrival_date = fields.Date(
        string="Expected Arrival Date",
        tracking=True
    )
    dispatch_date = fields.Date(
        string="Dispatch Date",
        tracking=True
    )
    critical_equipment = fields.Selection([
        ('none', "None Critical"),
        ('safety', "Safety Critical"),
        ('operations', "Operations Critical"),
        ('date_sensitive', "Date Sensitive"),
        ('hazard', "Hazard Material"),
    ], string="Criticality", help="Classification of the received items.")
    intended_vessel = fields.Char(
        string="Intended Vessel / Project",
        help="The vessel, project, or destination these goods are intended for."
    )
    customer_id = fields.Many2one(
        'res.partner',
        string="Customer",
        help="The ultimate customer."
    )
    customer_address = fields.Text(
        string="Customer Address",
    )
    unit_of_measure_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        help="Select the default unit of measure for this receipt."
    )
    amount = fields.Float(
        string="Total items", 
        help="Total items for each line",
        compute="compute_total_items"
    )
    is_warehouse_inventory = fields.Boolean(string='Warehouse Inventory?', default=lambda self: True if self.financial_id else False) #For demarcating the records in warehouse module from the reddit app
    
    # TRANSPORT
    truck_company_name = fields.Many2one('res.partner', string='Truck company Name')
    truck_reg = fields.Char(string='Truck registration No.')
    truck_type = fields.Char(string='Truck Type')
    truck_driver = fields.Many2one('res.partner', string='Driver details')
    truck_driver_phone = fields.Char(string='Driver Phone')
     
    waybill_from = fields.Char(string='Pickup Location?')
    waybill_to = fields.Char(string='Drop Off Location')
    waybill_date = fields.Datetime(string='Date of Transportation')
    waybill_expected_arrival_date = fields.Datetime(string='Expected Arrival')
    waybill_note = fields.Char(string='Waybill Note')
    

    # dispatch_move_ids_packages = fields.One2many(
    #     'stock.move',
    #     'dispatch_picking_id',
    #     string="Dispatch Moves"
    # )
    dispatch_picking_ids_packages = fields.Many2many(
        'stock.picking',
        'stock_picking_dispatch_rel',
        'stock_picking_id',
        'stock_dispatch_picking_id',
        string="Dispatch Picking"
    )
    dispatch_dest_location_id = fields.Many2one(
        'stock.location', 
        string="Dispatch location"
    )
    
    def confirm_dispatch(self):
        '''Checks if item exist in inventory and
        set status to dispatched
        '''
        # tt = self.env['stock.quant'].sudo()._get_available_quantity(self.env['product.product'].browse([10]), self.env['stock.location'].browse([18]), allow_negative=False) # or 0.0
        # raise ValidationError(f"{tt},{self.env['product.product'].browse([10])}, {self.env['stock.location'].browse([18])} ")
        for pck in self.dispatch_picking_ids_packages:
            for count, pml in enumerate(pck.move_ids_without_package, 1):
                tt_availability = self.env['stock.quant'].sudo()._get_available_quantity(pml.product_id, pml.location_id, allow_negative=False) # or 0.0
                if pml.quantity > tt_availability:
                    raise ValidationError(f"""
                                          At line {count}: The quantity to dispatch is lesser than the amount \n remaining in the inventory location {(pml.location_id.name)}. The product {(pml.product_id.name)} available quantity is {tt_availability}"""
                                          )
                # else:
                #     raise ValidationError("This dispatch does not have any product / items allocation during receipts")
                
            # pck.button_validate()
            if pck.state not in ['done']:
                raise ValidationError("please validate the dispatch operation before confirming")
        self.inventory_status = 'dispatch'
        
    is_dispatch = fields.Boolean()
    
    # def action_validate_owner_stock(self, picking):
    #     '''check the lines to ensure owner still have products in stock'''
    #     for rec in picking.move_ids_without_package:
    #         if rec.product_id.id:
    #             owner_stock_quants = self.env['stock.quant'].sudo().search([
    #             ('owner_id', '=', self.customer_id.id),
    #             ('product_id', '=', self.product_id.id),
    #             '|',('warehouse_id', '=', self.warehouse_id.id),
    #             ('location_id', '=', self.location_id.id)
    #             ])
    #             total_quantity = sum([qt.quantity for qt in owner_stock_quants])
    #             if total_quantity < 1:
    #                 items_to_remove
            
    def action_dispatch_moves(self):
        '''set is dispatch to true and enable dispatch functionality'''
        self.action_validate_owner_stock(self.customer_id)
        if self.move_ids_without_package:
            if not self.dispatch_picking_ids_packages:
                picking_id = self.copy()
                warehouse_picking_types = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', self.warehouse_id.id),
                    ('code', '=', 'outgoing'),
                    ], limit=1)
                picking_id.update({
                    "name": f"DISP/{picking_id.name}",
                    'location_id': self.location_dest_id.id,
                    'location_dest_id': self.dispatch_dest_location_id.id,
                    'related_inbound_shipment': self.id,
                    'inbound_picking_id': self.id,
                    'is_dispatch': True,
                    'picking_type_code': 'outgoing',
                    'picking_type_id': warehouse_picking_types and warehouse_picking_types.id,
                    'inventory_status': 'awaiting_dispatch',
                })
                 
                self.dispatch_picking_ids_packages = [(6, 0, [picking_id.id])]
                
                for pi in self.dispatch_picking_ids_packages:
                    for ml in pi.move_ids_without_package:
                        if ml.product_id.id:
                            owner_stock_quants = self.env['stock.quant'].sudo().search([
                            ('owner_id', '=', self.customer_id.id),
                            ('product_id', '=', ml.product_id.id),
                            '|',('warehouse_id', '=', self.warehouse_id.id),
                            ('location_id', '=', self.location_id.id)
                            ])
                            total_quantity = sum([qt.quantity for qt in owner_stock_quants])
                            if total_quantity < 1:
                                pi.move_ids_without_package = [(3, ml.id)]
            else:
                picking_id = self.dispatch_picking_ids_packages[0]
            picking_id.action_confirm()
            self.inventory_status = "awaiting_dispatch"
            return self.button_view_picking(picking_id.id)
        else:
            raise ValidationError("No stock move lines to Dispatch!!!")
    
    def print_way_bill(self):
        _logger.info("Printing with new updated template...............")
        return self.env.ref('warehousing_system.print_dispatch_waybill_report').report_action(self)
    
    def button_view_picking(self, pickingId):
        view_id = self.env.ref('warehousing_system.view_warehouse_inventory_form').id
        ret = {
            'name': "Dispatching",
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'stock.picking',
            'res_id': pickingId,
            'type': 'ir.actions.act_window',
            'domain': [],
            'target': 'current'
            }
        return ret     
                
    @api.depends('move_ids_without_package.no_of_items')
    def compute_total_items(self):
        for rec in self:
            if rec.move_ids_without_package:
                sum_items = sum([re.no_of_items for re in rec.mapped('move_ids_without_package')])
                rec.amount = sum_items if sum_items > 1 else len( rec.move_ids_without_package.ids)
            else:
                rec.amount = 0 
                
    
    def action_undo_storage(self):
        '''
        Undo storage by using Odoo's standard return mechanism.
        This approach is safer and maintains data integrity.
        '''
        records_to_reset = self.env.context.get('active_ids', [])
        records = self.browse(records_to_reset) if records_to_reset else self

        for record in records:
            if record.inventory_status not in ['allocated', 'done']:
                raise ValidationError("Can only undo storage from 'Allocated' or 'Stored' status.")

            active_dispatches = record.dispatch_picking_ids_packages.filtered(
                lambda p: p.state not in ['cancel', 'draft']
            )
            if active_dispatches:
                raise ValidationError(
                    "Cannot undo storage as there are active dispatch operations. "
                    "Please cancel or complete all related dispatch operations first."
                )

            if record.state == 'done':
                return_wizard = self.env['stock.return.picking'].with_context(
                    active_ids=record.ids, 
                    active_id=record.id,
                ).create({})
                
                return_action = return_wizard.create_returns()
                return_picking = self.env['stock.picking'].browse(return_action['res_id'])
                
                for move in return_picking.move_ids_without_package:
                    move.quantity = move.product_uom_qty
                    move.picked = True
                
                return_picking.with_context(skip_backorder=True).button_validate()

            record.write({
                'state': 'draft',
                'is_locked': False,
            })

            record.write({
                'inventory_status': 'draft',
                'actual_date_of_arrival': False,
            })

            if record.dispatch_picking_ids_packages:
                record.dispatch_picking_ids_packages.action_cancel()
                record.dispatch_picking_ids_packages = [(5, 0, 0)]

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    
    
    # @api.onchange('customer_id')
    # def _onchange_customer_id(self):
    #     if self.customer_id:
    #         self.owner_id = self.customer_id.id
    #         if self.picking_type_code == "outgoing":
    #             quant = self.env['stock.quant'].sudo()
    #             move = self.env['stock.move'].sudo()
    #             '''Get the owner stocks greater than 0 in given warehouse'''
    #             owner_stock_quants = quant.search([
    #                 ('owner_id', '=', self.customer_id.id),
    #                 # ('quantity', '>', 0),
    #                 '|',('warehouse_id', '=', self.warehouse_id.id),
    #                 ('location_id', '=', self.location_id.id)
    #                 ])
    #             list_items = {}
    #             # raise ValidationError(f"{owner_stock_quants}, {self.customer_id.id} {self.location_id.id}")
    #             for sq in owner_stock_quants:
    #                 '''Build stock moves dynamically'''
    #                 # product_items = {'id': False, 'name': "", 'qty': 0}
    #                 productId = sq.product_id.id
    #                 if str(productId) in list_items:
    #                     list_items[str(productId)]['qty'] += sq.available_quantity
    #                 else:
    #                     list_items[str(productId)] = {
    #                         'id': productId, 
    #                         'qty': sq.available_quantity, 
    #                         'name': sq.product_id.name
    #                         }
    #             for k, v in list_items.items():   
    #                 sq_vals = {
    #                     "name": f"{v.get('name')}-{v.get('id')}",
    #                     "product_id": v.get('id'),
    #                     "product_uom_qty": v.get('qty'),
    #                     "remaining_qty": v.get('qty'),
    #                     "product_uom": self.env['product.product'].sudo().browse([v.get('id')]).uom_id.id,
    #                     "picking_id": self.id,
    #                     "state": "draft",
    #                     "location_id": self.location_id.id,
    #                     "location_dest_id": self.location_dest_id.id,
    #                 }
    #                 self.move_ids_without_package = [(0, 0, sq_vals)]
                    
     
    # @api.onchange('origin')
    # def _onchange_origin(self):
    #     """Set financial_id when origin matches a memo code"""
    #     if self.origin and not self.financial_id:
    #         memo = self.env['memo.model'].search([
    #             ('code', '=', self.origin),
    #             ('memo_type.memo_key', 'in', ['transport', 'warehouse'])
    #         ], limit=1)
    #         if memo:
    #             self.financial_id = memo
    #         elif self.origin:
    #             memo = self.env['memo.model'].search([
    #                 ('code', 'ilike', self.origin),
    #                 ('memo_type.memo_key', 'in', ['transport', 'warehouse'])
    #             ], limit=1)
    #             if memo:
    #                 self.financial_id = memo
    #                 self.origin = memo.code
                    
            
    @api.onchange('financial_id')
    def _onchange_financial_id_for_items(self):
        for pick in self:
            if pick.financial_id:
                # self.supplier_po_number = self.financial_id.name or ''
                # self.origin = self.financial_id.code
                self.origin = self.financial_id.name
                self.partner_id = self.financial_id.client_id.id
                self.customer_id = self.financial_id.client_id.id
                self.owner_id = self.financial_id.client_id.id
                if not self.receiving_supplier_id and self.financial_id.client_id:
                    self.receiving_supplier_id = self.financial_id.client_id
                pick.move_ids_without_package = [(5, 0, 0)]
                src_loc = pick.location_id.id \
                        or pick.picking_type_id.default_location_src_id.id
                dst_loc = pick.location_dest_id.id \
                        or pick.picking_type_id.default_location_dest_id.id
                new_moves = []
                if pick.financial_id.waybill_ids:
                    for wb in pick.financial_id.waybill_ids:
                        uom = self.env['uom.uom'].search(
                            [('name', '=', wb.uom)], limit=1
                        )
                        new_moves.append((0, 0, {
                            'name': wb.product_id.display_name,
                            'product_id': wb.product_id.id,
                            'product_uom_qty': wb.quantity or 0.0,
                            'product_uom': uom.id or wb.product_id.uom_id.id or False,
                            'location_id': src_loc,
                            'location_dest_id': dst_loc,
                            'description_picking': wb.waybill_desc or '',
                        }))
                    pick.move_ids_without_package = new_moves
                    self.inventory_status = "arrived"
            # else:
            #     self.inventory_status = "arrived"
            #     self.state = "draft"
            
    
    # @api.onchange('customer_id')
    # def _onchange_customer_id_set_owner(self):
    #     if self.customer_id:
    #         if self.picking_type_code == 'incoming':
    #             self.owner_id = self.customer_id.id
    #         for move in self.move_ids_without_package:
    #             move.restrict_partner_id = self.customer_id.id
    #     else:
    #         self.owner_id = False
    #         for move in self.move_ids_without_package:
    #             move.restrict_partner_id = False
            
    # @api.model
    # def search_memo_codes(self, query):
    #     """Search method for autocomplete functionality"""
    #     if not query or len(query) < 2:
    #         return []
            
    #     domain = [
    #         ('code', 'ilike', query),
    #         ('memo_type.memo_key', 'in', ['transport', 'warehouse'])
    #     ]
        
    #     # Search with both 'starts with' and 'contains' for better results
    #     memos_starts_with = self.env['memo.model'].search([
    #         ('code', '=ilike', f'{query}%'),
    #         ('memo_type.memo_key', 'in', ['transport', 'warehouse'])
    #     ], limit=5)
        
    #     memos_contains = self.env['memo.model'].search([
    #         ('code', 'ilike', query),
    #         ('memo_type.memo_key', 'in', ['transport', 'warehouse']),
    #         ('id', 'not in', memos_starts_with.ids)
    #     ], limit=5)
        
    #     all_memos = memos_starts_with + memos_contains
        
    #     return [{
    #         'id': memo.id,
    #         'code': memo.code,
    #         'name': memo.name or memo.code,
    #         'display_name': f"{memo.code} - {memo.name}" if memo.name and memo.name != memo.code else memo.code
    #     } for memo in all_memos[:10]]  # Limit to 10 results
                
    # inbound_picking_id = fields.Many2one(
    #     'stock.picking',
    #     string="Related Inbound Shipment",
    #     domain=[('picking_type_id.code', '=', 'incoming')],
    #     help="Select the receipt operation that brought these goods into stock."
    # )

    def button_financial_file(self):
        view_id = self.env.ref('company_memo.tree_memo_model_view2').id
        ret = {
            'name': "Financial File",
            'view_mode': 'tree',
            'view_id': view_id,
            'view_type': 'tree',
            'res_model': 'memo.model',
            # 'res_id': self.financial_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain' :[('id', 'in', [self.financial_id.id])]
            }
        return ret
    
    def action_confirm(self):
        res = super(WarehouseInventory, self).action_confirm()
        self.inventory_status = 'allocated' if not self.dispatch_dest_location_id else 'awaiting_dispatch'
        self.state = 'assigned'
        return res
    
    def action_set_draft(self):
        self.inventory_status = 'draft' 
        self.state = 'draft'
        for r in self.move_ids:
            r.state = "draft"
        for r in self.move_ids_without_package:
            r.state = "draft"
    
    def button_validate(self):
        'validate transport details'
        if self.is_dispatch:
            if not self.truck_company_name or not self.truck_reg or not self.truck_type \
                or not self.truck_driver or not self.waybill_from or not self.waybill_to or not self.waybill_date:
                raise ValidationError('Please ensure all transportation details are filled')
        for rec in self.move_ids_without_package:
            if rec.product_uom_qty <= 0:
                raise ValidationError(f'{rec.product_id.name} move lines quantity contains negative stock. It must be above 0')
            rec.update({
                'quantity': rec.product_uom_qty,
                # 'product_qty': rec.product_uom_qty,
            })
        _logger.info("Run........................1")
        
        res = super(WarehouseInventory, self).button_validate()
        self.inventory_status = 'done' if not self.dispatch_dest_location_id and self.inventory_status not in 'awaiting_dispatch' else 'dispatch'
        return res

    
    # def button_validate(self):
    #     'validate transport details'
    #     if self.is_dispatch:
    #         if not self.truck_company_name or not self.truck_reg or not self.truck_type \
    #             or not self.truck_driver or not self.waybill_from or not self.waybill_to or not self.waybill_date:
    #             raise ValidationError('Please ensure all transportation details are filled')
    #     else:
    #         if self.picking_type_code == 'incoming' and self.customer_id:
    #             self.owner_id = self.customer_id.id
                
    #             for move in self.move_ids_without_package:
    #             # Setting owner on move_lines is the key for correct quant creation
    #                 for move_line in move.move_line_ids:
    #                     move_line.owner_id = self.customer_id.id
                    
    #     for rec in self.move_ids_without_package:
    #         if rec.product_uom_qty <= 0:
    #             raise ValidationError(f'{rec.product_id.name} move lines quantity contains negative stock. It must be above 0')
    #         rec.update({
    #             'quantity': rec.product_uom_qty,
    #             # 'product_qty': rec.product_uom_qty,
    #         })
        
    #     res = super(WarehouseInventory, self).button_validate()
    #     self.inventory_status = 'done' if not self.dispatch_dest_location_id and self.inventory_status not in 'awaiting_dispatch' else 'dispatch'
    
    
    def action_cancel(self):
        res = super(WarehouseInventory, self).action_cancel()
        self.inventory_status = 'cancelled'
        return res
    
    length_mtr = fields.Float(compute='_compute_move_item_properties')
    width_mtr = fields.Float(compute='_compute_move_item_properties')
    height_mtr = fields.Float(compute='_compute_move_item_properties')
    volume_m3 = fields.Float(compute='_compute_move_item_properties')
    weight_kg = fields.Float(compute='_compute_move_item_properties')
    area_chargeable = fields.Float(compute='_compute_move_item_properties', store=True)

    @api.depends('move_ids_without_package', 'move_ids_without_package.product_id', 'move_ids_without_package.length_mtr', 'move_ids_without_package.height_mtr', 'move_ids_without_package.width_mtr', 'move_ids_without_package.weight_kg')
    def _compute_move_item_properties(self):
        for picking in self:
            items_length_mtr = picking.move_ids_without_package.mapped('length_mtr')
            items_width_mtr = picking.move_ids_without_package.mapped('width_mtr')
            picking.length_mtr = sum(items_length_mtr)
            picking.width_mtr = sum(items_width_mtr)
            max_width = max(items_width_mtr, default=0.0)
            picking.area_chargeable = sum([item * max_width for item in items_length_mtr])
            picking.height_mtr = sum(picking.move_ids_without_package.mapped('height_mtr'))
            picking.volume_m3 = sum(picking.move_ids_without_package.mapped('volume_m3'))
            picking.weight_kg = sum(picking.move_ids_without_package.mapped('weight_kg'))
            
            
    @api.model
    def get_context_for_product_search(self):
        """Get context data for product filtering in stock moves"""
        context = {}
        if self.partner_id:
            context['filter_customer_id'] = self.partner_id.id
        if self.location_id:
            context['filter_location_id'] = self.location_id.id
        if self.location_dest_id:
            context['filter_dest_location_id'] = self.location_dest_id.id
        if self.picking_type_id:
            context['filter_picking_type_id'] = self.picking_type_id.id
            context['filter_picking_code'] = self.picking_type_id.code
        return context
    
    def get_base_domain(self, filters):
        base_domain = ['|',('is_warehouse_inventory','=', True),('financial_id', '!=', False)]
         
        if filters.get('client') and filters['client'].strip():
            base_domain.append(('customer_id.name', 'ilike', filters['client'].strip()))
            _logger.info(f'Customer: {base_domain}')
            
        if filters.get('vessel') and filters['vessel'].strip():
            base_domain.append(('intended_vessel', 'ilike', filters['vessel'].strip()))
            _logger.info(f'Vessel: {base_domain}')
        
        return base_domain
    
    def _get_move_base_domain(self, filters=None):
        if not filters:
            filters = {}

        picking_domain = self.get_base_domain(filters)
        if not picking_domain:
            return []

        pickings = self.search(picking_domain)
        if not pickings:
            return [('id', '=', 0)] 

        return [('picking_id', 'in', pickings.ids)]
    
    # def _domain_total_in_stock(self):
    #     """Domain for stock.move items that are physically in the warehouse.
    #        'assigned' state is a good proxy for received, processed, and waiting for dispatch.
    #     """
    #     return [
    #         ('inventory_status', 'in', ['arrived', 'allocated', 'done', 'awaiting_dispatch' ])
    #         ]
    
    def total_inventory_item_domain(self):
        return [
            ('inventory_status', 'in', ['draft','arrived', 'allocated', 'done' , 'awaiting_dispatch']),
            ('actual_date_of_arrival', '<=', fields.Date.today()), 
            # ('picking_id.picking_type_code', '=', 'incoming'),
            '|', ('financial_id', '!=', False), ('is_warehouse_inventory', '=', True)
            ]
    
    def expected_date_today_domain(self):
        return [('scheduled_date', '=', fields.Date.today()), 
                ('financial_id', '!=', False), 
                ('inventory_status', 'not in', ['cancelled']),]
        
    def expected_date_later_domain(self):
        return ['&', '&', '&', ('scheduled_date', '>', fields.Date.today()),
                '|', ('actual_date_of_arrival', '=', False),
                ('actual_date_of_arrival', '>', fields.Date.today()),
                ('financial_id', '!=', False), 
                ('inventory_status', 'not in', ['cancelled']),]
    
    # def _domain_expected_on(self, days_from_now):
    #     """Domain for stock.move items whose parent picking is scheduled for a specific date."""
    #     target_date = fields.Date.today() + timedelta(days=days_from_now)
    #     return [
    #         ('picking_id.state', 'in', ['assigned', 'confirmed', 'waiting']),
    #         ('picking_id.scheduled_date', '=', target_date)]
        
    def _actual_arrival_date_domain_90_days(self):
        """This seems to mean items IN STOCK for more than 90 days"""
        ninety_days_ago = fields.Date.today() - timedelta(days=90)
        return [
            ('actual_date_of_arrival', '<', ninety_days_ago),
            ('inventory_status', 'in', ['arrived', 'allocated', 'done']),
            ('picking_type_code', '=', 'incoming'),
            '|', ('financial_id', '!=', False), ('is_warehouse_inventory', '=', True)
        ]
        
    def _domain_expected_today(self):
        """Domain for stock.move items whose parent picking is scheduled for today."""
        return [
            ('picking_id.state', 'in', ['assigned', 'confirmed', 'waiting']),
            ('picking_id.actual_date_of_arrival', '=', fields.Date.today())
        ]
    
    def _domain_expected_later(self):
        """Domain for stock.move items whose parent picking is scheduled for a specific date."""
        return [
            ('inventory_status', 'in', ['draft']),
            ('picking_id.scheduled_date', '>', fields.Date.today())
        ]
    def _domain_pending_allocation(self):
        """Domain for stock.move items that have been confirmed but not yet located/reserved."""
        return [('state', '=', 'confirmed')]
    
    
    def _domain_dispatched_on(self, days_from_now):
        """Domain for stock.move items from OUTGOING pickings scheduled for a specific date."""
        target_date = fields.Date.today() + timedelta(days=days_from_now)
        return [
            ('picking_id.picking_type_code', '=', 'outgoing'),
            ('picking_id.state', 'in', ['assigned', 'confirmed']),
            ('picking_id.scheduled_date', '=', target_date)
        ]
        
    def _domain_dispatched_past_90_days(self):
        """This seems to mean items IN STOCK for more than 90 days"""
        ninety_days_ago = fields.Date.today() - timedelta(days=90)
        return [
            ('picking_id.picking_type_code', '=', 'incoming'),
            ('date', '<=', ninety_days_ago),
            ('state', '=', 'assigned')
        ]
    
    def to_be_put_in_stock_domain(self):
        return [
            ('inventory_status', 'in', ['arrived', 'allocated']),
            ('financial_id', '!=', False)]
    
    
    def without_allocated_storage_domain(self):
        return [
            # ('warehouse_id', '=', False),
            ('financial_id', '!=', False),
            ('move_ids_without_package', '!=', False),
            ('inventory_status', '=', 'allocated'),
        ]
    
    def labels_to_be_printed_domain(self):
        return [
            ('inventory_status', 'not in', ['draft', 'cancelled']),
            ('financial_id', '!=', False),
            ('move_ids_without_package', '!=', False),
            ('move_ids_without_package.is_label_printed', '=', False)
        ]
        
    def _domain_labels_to_print(self):
        """Domain for stock.move items that have not yet had their label printed."""
        return [
            ('state', 'not in', ('cancel')), # Only for active records
            ('is_label_printed', '=', False)
        ]
        
    def open_osd_inventory_domain(self):
        return [
            ('inventory_status', '=', 'arrived'),
            ('financial_id', '!=', False),
        ]
        
    def critical_items_domain(self):
        return [
            ('warehouse_id', '!=', False),
            ('inventory_status', '=', 'allocated'),
            ('financial_id', '!=', False)
        ]
        
    def pending_dispatched_items_domain(self):
        return [
            ('picking_type_code','=', 'outgoing'),
            ('inventory_status', '=', 'awaiting_dispatch'),
            ('is_warehouse_inventory', '=', True),
            ('move_ids_without_package', '!=', False),
        ]
        
    def _safe_zone_ids(self, xml_ids):
        """Resolve a list of external XML IDs to existing record IDs, ignoring missing ones."""
        ids = []
        for xmlid in xml_ids:
            try:
                rec = self.env.ref(xmlid)
            except ValueError:
                continue
            if rec:
                ids.append(rec.id)
        return ids

    def get_mainWarehouse_utilization_domain(self):
        zones = self._safe_zone_ids([
            '__import__.loc_main_warehouse',
            '__import__.loc_security_storage_2',
        ])
        if not zones:
            return [('id', '=', 0)]
        _logger.info(f"Found Location!!!")
        return [
            ('inventory_status', '=', 'done'),
            ('financial_id', '!=', False),
            '|',
              ('location_dest_id', 'child_of', zones),
              ('move_ids_without_package.location_dest_id', 'child_of', zones),
        ]

    def get_bondedWarehouse_utilization_domain(self):
        zones = self._safe_zone_ids([
            '__import__.loc_security_storage_1',
        ])
        if not zones:
            return [('id', '=', 0)]
        return [
            ('financial_id', '!=', False),
            ('inventory_status', '=', 'done'),
            '|',
              ('location_dest_id', 'child_of', zones),
              ('move_ids_without_package.location_dest_id', 'child_of', zones),
        ]

    def get_coveredStacking_utilization_domain(self):
        zones = self._safe_zone_ids([
            '__import__.loc_covered_stacking_area',
            '__import__.loc_security_storage_3',
        ])
        if not zones:
            return [('id', '=', 0)]
        return [
            ('inventory_status', '=', 'done'),
            ('financial_id', '!=', False),
            '|',
              ('location_dest_id', 'child_of', zones),
              ('move_ids_without_package.location_dest_id', 'child_of', zones),
        ]

    def get_openStacking_utilization_domain(self):
        zones = self._safe_zone_ids([
            '__import__.loc_open_stacking_area_1',
            '__import__.loc_open_stacking_area_2',
            '__import__.loc_open_stacking_area_3',
        ])
        if not zones:
            return [('id', '=', 0)]
        return [
            ('inventory_status', '=', 'done'),
            ('financial_id', '!=', False),
            '|',
              ('location_dest_id', 'child_of', zones),
              ('move_ids_without_package.location_dest_id', 'child_of', zones),
        ]
    
    
    def get_critical_items_domain(self):
        return [('move_ids_without_package.item_classification_critical', '=', True)]

    def get_dangerous_goods_domain(self):
        return [('move_ids_without_package.item_classification_dangerous', '=', True)]

    def get_temperature_sensitive_domain(self):
        return [('move_ids_without_package.item_classification_temperature', '=', True),
                ('picking_type_code','=', 'incoming')]
    
    def get_utilizationArea(self, domain):
        _logger.info(f"Domain logging {domain}")
        if isinstance(domain, list):
            _logger.info("Area chargeable calculated here!!")
            area = sum(
                self.env['stock.picking']
                    .search(domain)
                    .mapped('area_chargeable'))
            _logger.info(f"Area is {area}")
            return area
        else:
            return 0
    
    
    @api.model
    def get_warehouse_dashboard_data(self, filters=None):
        """
        This method fetches all the necessary data for the warehouse dashboard
        Returns a dictionary with counts for different inventory statuses
        
        Args:
            filters: A dictionary with filter values
                - client: Text to search in customer_id.name
                - fileType: Inventory status
                - projectNo: Supplier PO number
                - month: Month for create_date
                - year: Year for create_date
        """
        # _logger.info(f"Method called with args: {repr(locals())}")
        # _logger.info(f"self: {self}")
        # _logger.info(f"filters parameter: {repr(filters)}")
        if not filters:
            filters = {}
        # _logger.info(f"Filters type: {type(filters)}")
        # _logger.info(f"Filters content: {filters}")
        # _logger.info(f"Filters repr: {repr(filters)}")
            
        base_domain = self.get_base_domain(filters) or []
        _logger.info(f'Base: Domain: {base_domain}')
        
        total_inventory_item = self.search_count(base_domain + self.total_inventory_item_domain())
        expected_tomorrow = self.search_count(base_domain + self.expected_date_today_domain())
        expected_today = self.search_count(base_domain + self.expected_date_later_domain())
        to_be_put_in_stock = self.search_count(base_domain + self.to_be_put_in_stock_domain())
        without_allocated_storage = self.search_count(base_domain + self.without_allocated_storage_domain())
        
        not_printed_labels = self.search(base_domain + self.labels_to_be_printed_domain())
        labels_to_be_printed = len(not_printed_labels)
        
        longer_than_90_days = self.search_count(base_domain + self._actual_arrival_date_domain_90_days())
        
        open_osd_inventory = self.search_count(base_domain + self.open_osd_inventory_domain())
        
        # displaced_items = self.search_count(base_domain + self.displaced_items_domain())
        
        PendingdispatchedItems = self.search_count(base_domain + self.pending_dispatched_items_domain())
        
        move_base_domain = self._get_move_base_domain(filters)
        _logger.info(f'Base Domain for stock.move: {move_base_domain}')


        critical_stock_items = self.search_count(base_domain + self.get_critical_items_domain())
        dangerous_goods = self.search_count(base_domain + self.get_dangerous_goods_domain())
        temperature_sensitive = self.search_count(base_domain + self.get_temperature_sensitive_domain())
        
        main_domain = base_domain + self.get_mainWarehouse_utilization_domain()
        bonded_domain = base_domain + self.get_bondedWarehouse_utilization_domain()
        covered_domain = base_domain + self.get_coveredStacking_utilization_domain()
        open_domain = base_domain + self.get_openStacking_utilization_domain()
        
        mainWarehouseUtilization = self.get_utilizationArea(main_domain)
        bondedWarehouseUtilization = self.get_utilizationArea(bonded_domain)
        coveredStackingUtilization = self.get_utilizationArea(covered_domain)
        openStackingUtilization = self.get_utilizationArea(open_domain)
        
        result = {
            'totalInventoryItem': total_inventory_item,
            'expectedTomorrow': expected_tomorrow,
            'expectedToday': expected_today,
            'toBePutInStock': to_be_put_in_stock,
            'withoutAllocatedStorage': without_allocated_storage,
            'labelsToBePrinted': labels_to_be_printed,
            'longerThan90Days': longer_than_90_days,
            'openOSDInventory': open_osd_inventory,
            'criticalStockItems': critical_stock_items,
            'dangerousGoods': dangerous_goods,
            'temperatureSensitive': temperature_sensitive,
            'PendingdispatchedItems': PendingdispatchedItems,
            'mainWarehouseUtilization': "%.2f" % mainWarehouseUtilization,
            'bondedWarehouseUtilization': "%.2f" % bondedWarehouseUtilization,
            'coveredStackingUtilization': "%.2f" % coveredStackingUtilization,
            'openStackingUtilization': "%.2f" % openStackingUtilization
        }
        
        _logger.info(f"Dashboard data: {result}")
        
        return result

    
    
    @api.model
    def get_action(self, action_data=None):
        action_data = action_data or {}
        card = action_data.get('cardSelected')

        action = None
        domain = []

        action_ref = 'warehousing_system.action_warehouse_inventory_receipts'

        move_action_cards = []

        if card in move_action_cards:
            action_ref = 'warehousing_system.action_stock_move_tree_view'
            domain_map = {
                'criticalStockItems': self.get_critical_items_domain,
                'dangerousGoods': self.get_dangerous_goods_domain,
                'temperatureSensitive': self.get_temperature_sensitive_domain,
            }
            if card in domain_map:
                domain = domain_map[card]()

            if action_data.get('filterData'):
                move_base_domain = self._get_move_base_domain(action_data['filterData'])
                if move_base_domain:
                    domain += move_base_domain
        else:
            domain_map = {
                'totalInventoryItem': self.total_inventory_item_domain,
                'expectedTomorrow': lambda: self.expected_date_today_domain(),
                'expectedToday': lambda: self.expected_date_later_domain(),
                'toBePutInStock': self.to_be_put_in_stock_domain,
                'withoutAllocatedStorage': self.without_allocated_storage_domain,
                'labelsToBePrinted': self.labels_to_be_printed_domain,
                'longerThan90Days': self._actual_arrival_date_domain_90_days,
                'openOSDInventory': self.open_osd_inventory_domain,
                'PendingdispatchedItems': self.pending_dispatched_items_domain,
                'criticalStockItems': self.get_critical_items_domain,
                'dangerousGoods': self.get_dangerous_goods_domain,
                'temperatureSensitive': self.get_temperature_sensitive_domain,
                'mainWarehouseUtilization': self.get_mainWarehouse_utilization_domain,
                'bondedWarehouseUtilization': self.get_bondedWarehouse_utilization_domain,
                'coveredStackingUtilization': self.get_coveredStacking_utilization_domain,
                'openStackingUtilization': self.get_openStacking_utilization_domain
            }
            if card in domain_map:
                domain = domain_map[card]()

            if action_data.get('filterData'):
                base_domain = self.get_base_domain(action_data['filterData']) or []
                if base_domain:
                    domain += base_domain

        action = self.env["ir.actions.actions"]._for_xml_id(action_ref)
        action['domain'] = domain

        if action_data.get('title'):
            action['display_name'] = action_data['title']

        _logger.info(f"Final Action Domain = {action['domain']}")
        return {'action': action}
    
    
    #Public Methods
    @api.model
    def _get_customer_secure_base_domain(self, filters=None):
        """
        Creates a secure base domain for the logged-in portal user.
        - If user is an 'Inventory Admin', they bypass the partner filter.
        - Otherwise, they only see their own records.
        """
        filters = filters or {}
        user = request.env.user
        domain = ['|', ('is_warehouse_inventory', '=', True), ('financial_id', '!=', False)]

        if user.has_group('warehousing_system.group_inventory_admin'):
            pass  # Admin can see all records
        else:
            partner = user.partner_id
            domain.append(('customer_id', '=', partner.id))

        if filters.get('client') and filters['client'].strip():
            domain.append(('customer_id.name', 'ilike', filters['client'].strip()))
            
        if filters.get('vessel') and filters['vessel'].strip():
            domain.append(('intended_vessel', 'ilike', filters['vessel'].strip()))
            
        location_id = filters.get('location_id')
        if location_id and location_id.isdigit():
            domain.append(('move_ids_without_package.location_dest_id', '=', int(location_id)))
            
        return domain

    @api.model
    def get_customer_warehouse_dashboard_data(self, filters=None):
        """
        Customer version of get_warehouse_dashboard_data.
        Reuses internal methods but applies customer security filter.
        """
        if not filters:
            filters = {}
            
        base_domain = self._get_customer_secure_base_domain(filters) or []
        _logger.info(f'Customer Base Domain: {base_domain}')
        
        total_inventory_item = self.search_count(base_domain + self.total_inventory_item_domain())
        expected_tomorrow = self.search_count(base_domain + self.expected_date_later_domain())
        expected_today = self.search_count(base_domain + self.expected_date_today_domain())
        to_be_put_in_stock = self.search_count(base_domain + self.to_be_put_in_stock_domain())
        without_allocated_storage = self.search_count(base_domain + self.without_allocated_storage_domain())
        
        not_printed_labels = self.search(base_domain + self.labels_to_be_printed_domain())
        labels_to_be_printed = len(not_printed_labels)
        
        longer_than_90_days = self.search_count(base_domain + self._actual_arrival_date_domain_90_days())
        open_osd_inventory = self.search_count(base_domain + self.open_osd_inventory_domain())
        pending_dispatched_items = self.search_count(base_domain + self.pending_dispatched_items_domain())
        
        critical_stock_items = self.search_count(base_domain + self.get_critical_items_domain())
        dangerous_goods = self.search_count(base_domain + self.get_dangerous_goods_domain())
        temperature_sensitive = self.search_count(base_domain + self.get_temperature_sensitive_domain())
        
        main_domain = base_domain + self.get_mainWarehouse_utilization_domain()
        bonded_domain = base_domain + self.get_bondedWarehouse_utilization_domain()
        covered_domain = base_domain + self.get_coveredStacking_utilization_domain()
        open_domain = base_domain + self.get_openStacking_utilization_domain()
        
        main_warehouse_utilization = self.get_utilizationArea(main_domain)
        bonded_warehouse_utilization = self.get_utilizationArea(bonded_domain)
        covered_stacking_utilization = self.get_utilizationArea(covered_domain)
        open_stacking_utilization = self.get_utilizationArea(open_domain)
        
        result = {
            'totalInventoryItem': total_inventory_item,
            'expectedTomorrow': expected_tomorrow,
            'expectedToday': expected_today,
            'toBePutInStock': to_be_put_in_stock,
            'withoutAllocatedStorage': without_allocated_storage,
            'labelsToBePrinted': labels_to_be_printed,
            'longerThan90Days': longer_than_90_days,
            'openOSDInventory': open_osd_inventory,
            'pendingDispatchedItems': pending_dispatched_items,
            'criticalStockItems': critical_stock_items,
            'dangerousGoods': dangerous_goods,
            'temperatureSensitive': temperature_sensitive,
            'mainWarehouseUtilization': "%.2f" % main_warehouse_utilization,
            'bondedWarehouseUtilization': "%.2f" % bonded_warehouse_utilization,
            'coveredStackingUtilization': "%.2f" % covered_stacking_utilization,
            'openStackingUtilization': "%.2f" % open_stacking_utilization
        }
        
        _logger.info(f"Customer Dashboard data: {result}")
        return result

    @api.model
    def get_customer_dashboard_detail(self, action_data=None):
        """
        Customer version of get_action method.
        Returns detailed stock.picking records with customer security applied.
        """
        action_data = action_data or {}
        card = action_data.get('cardSelected')
        filters = action_data.get('filterData', {})
        
        base_domain = self._get_customer_secure_base_domain(filters) or []
        
        domain_map = {
            'totalInventoryItem': self.total_inventory_item_domain,
            'expectedTomorrow': lambda: self.expected_date_later_domain(1),
            'expectedToday': lambda: self.expected_date_today_domain(),
            'toBePutInStock': self.to_be_put_in_stock_domain,
            'withoutAllocatedStorage': self.without_allocated_storage_domain,
            'labelsToBePrinted': self.labels_to_be_printed_domain,
            'longerThan90Days': self._actual_arrival_date_domain_90_days,
            'openOSDInventory': self.open_osd_inventory_domain,
            'pendingDispatchedItems': self.pending_dispatched_items_domain,
            'criticalStockItems': self.get_critical_items_domain,
            'dangerousGoods': self.get_dangerous_goods_domain,
            'temperatureSensitive': self.get_temperature_sensitive_domain,
            'mainWarehouseUtilization': self.get_mainWarehouse_utilization_domain,
            'bondedWarehouseUtilization': self.get_bondedWarehouse_utilization_domain,
            'coveredStackingUtilization': self.get_coveredStacking_utilization_domain,
            'openStackingUtilization': self.get_openStacking_utilization_domain,
            # Some aliases for common views
            'all_inventory': self.total_inventory_item_domain,
            'dispatchedItems': self.pending_dispatched_items_domain,
            'inbound': self.to_be_put_in_stock_domain,
            'outbound': self.pending_dispatched_items_domain,
        }
        
        card_domain = []
        if card in domain_map:
            domain_method = domain_map[card]
            card_domain = domain_method() if callable(domain_method) else domain_method
        
        final_domain = base_domain + card_domain
        
        records = self.search(final_domain, limit=200)  # limit for safety
        
        headers = [
            {'key': 'name', 'label': 'Reference'},
            {'key': 'customer', 'label': 'Customer'},
            {'key': 'vessel', 'label': 'Vessel'},
            {'key': 'inventory_status', 'label': 'Status'},
            {'key': '', 'label': 'Scheduled Date'},
            {'key': 'area_chargeable', 'label': 'Area (m²)'},
        ]
        
        result_records = []
        for record in records:
            result_records.append({
                'name': record.name or '',
                'customer': record.customer_id.name if record.customer_id else '',
                'vessel': record.intended_vessel or '',
                'inventory_status': dict(record._fields['inventory_status'].selection).get(record.inventory_status, record.inventory_status) if hasattr(record, 'inventory_status') else '',
                'scheduled_date': record.scheduled_date.strftime('%Y-%m-%d') if record.scheduled_date else '',
                'area_chargeable': f"{record.area_chargeable:.2f}" if hasattr(record, 'area_chargeable') and record.area_chargeable else '0.00',
            })
        
        return {
            'headers': headers,
            'records': result_records
        }

    @api.model
    def get_customer_action(self, action_data=None):
        """
        Customer version of get_action method.
        Returns action configuration for opening detailed views.
        """
        action_data = action_data or {}
        card = action_data.get('cardSelected')
        
        base_domain = self._get_customer_secure_base_domain(action_data.get('filterData', {})) or []
        
        domain_map = {
            'totalInventoryItem': self.total_inventory_item_domain,
            'expectedTomorrow': lambda: self.expected_date_later_domain(),
            'expectedToday': lambda: self.expected_date_today_domain(),
            'toBePutInStock': self.to_be_put_in_stock_domain,
            'withoutAllocatedStorage': self.without_allocated_storage_domain,
            'labelsToBePrinted': self.labels_to_be_printed_domain,
            'longerThan90Days': self._actual_arrival_date_domain_90_days,
            'openOSDInventory': self.open_osd_inventory_domain,
            'pendingDispatchedItems': self.pending_dispatched_items_domain,
            'criticalStockItscheduled_dateems': self.get_critical_items_domain,
            'dangerousGoods': self.get_dangerous_goods_domain,
            'temperatureSensitive': self.get_temperature_sensitive_domain,
            'mainWarehouseUtilization': self.get_mainWarehouse_utilization_domain,
            'bondedWarehouseUtilization': self.get_bondedWarehouse_utilization_domain,
            'coveredStackingUtilization': self.get_coveredStacking_utilization_domain,
            'openStackingUtilization': self.get_openStacking_utilization_domain,
        }
        
        domain = []
        if card in domain_map:
            domain_method = domain_map[card]
            domain = domain_method() if callable(domain_method) else domain_method
        
        final_domain = base_domain + domain
        
        action = self.env["ir.actions.actions"]._for_xml_id('warehousing_system.action_warehouse_inventory_receipts')
        action['domain'] = final_domain
        
        if action_data.get('title'):
            action['display_name'] = action_data['title']
        
        _logger.info(f"Customer Action Domain = {final_domain}")
        return {'action': action}