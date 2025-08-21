from odoo import api, fields, models, _
import io
import base64
import qrcode
from odoo.exceptions import ValidationError
from odoo.osv import expression
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    #item descrition = description_picking
    #length (in mtr) = 
    active = fields.Boolean(default=True)
    is_label_printed = fields.Boolean(String="Label Printed")
    length_mtr = fields.Float(String="Length (m)", compute="_compute_properties", store=True)
    #width (in mtr) =
    width_mtr = fields.Float(String="Width (m)", compute="_compute_properties", store=True)
    # Height (in mtr) =
    height_mtr = fields.Float(String="Height (m)", compute="_compute_properties", store=True)
    #Item value (Naira)
    item_value = fields.Float(String="Items Value")
    #Customer Reference = restrict_partner_id
    #Amount of inner package per item = product_qty product_uom product_uom_qty quantity
    #Weight (kg) per Item
    weight_kg = fields.Float(String="Weight per item (Kg)", compute="_compute_properties", store=True)
    
    #Space occupied in m2
    area_m2 = fields.Float(String="Space occupied (m2)",
                           compute="compute_stockmove_measure"
    )
    
    @api.depends('move_line_ids.quantity', 'move_line_ids.length_mtr', 'move_line_ids.width_mtr', 'move_line_ids.height_mtr', 'move_line_ids.weight_per_item', 'move_line_ids.item_value')
    def _compute_properties(self):
        for move in self:
            move.length_mtr = sum(move.move_line_ids.mapped('length_mtr'))
            move.width_mtr = sum(move.move_line_ids.mapped('width_mtr'))
            move.height_mtr = sum(move.move_line_ids.mapped('height_mtr'))
            move.weight_kg = sum(move.move_line_ids.mapped('weight_per_item'))
            move.item_value = sum(move.move_line_ids.mapped('item_value'))

    @api.depends('move_line_ids','move_line_ids.area_m2', 'move_line_ids.volume_m3')
    def compute_stockmove_measure(self):
        for ml in self:
            ml.area_m2 = sum(ml.move_line_ids.mapped('area_m2'))
            ml.volume_m3 = sum(ml.move_line_ids.mapped('volume_m3'))
            
    #Space Occupied in m3
    volume_m3 = fields.Float(String="Space occupied (m3)", compute="compute_stockmove_measure")
    area_chargeable = fields.Float(String="Chargeable Space(m2)")
    
    show_details_visible = fields.Boolean('Details Visible', default=True)
    no_of_items = fields.Float('No. of items', help="No of item in each box")
    item_picture = fields.Binary("Picture")
    qr_code = fields.Binary(string="QR Code")
    dispatch_picking_id = fields.Many2one(
        'stock.picking',
        string="Dispatch Stock Picking",
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'stock_move_attachment_ids_rel',
        'attachment_id',
        'stock_id'
    )
    critical_equipment = fields.Selection([
        ('none', "None Critical"),
        ('safety', "Safety Critical"),
        ('operations', "Operations Critical"),
        ('date_sensitive', "Date Sensitive"),
        ('hazard', "Hazard Material"),
    ], string="Critical Equipment")
    
    item_classification_critical = fields.Boolean(
        string="Critical")
    item_classification_dangerous = fields.Boolean(
        string="Dangerous Goods",
        help="Class of Dangerous Goods" )
    
    dangerous_goods_class = fields.Selection(selection=[
        ('explosives', 'Class 1- Explosives'),
        ('flammable_gases', 'Class 2 - Fammable Gases'),
        ('flammable_liquids', 'Class 3 - Flammable Liquids'),
        ('flammable_solids', 'Class 4 - Flammable Solids'),
        ('oxidising', 'Class 5 - Oxidising'),
        ('toxic_and_infectious', 'Class 6 - Toxic & Infectious'),
        ('radioactive', 'Class 7 - Radioactive'),
        ('corrosives', 'Class 8 - Corrosives'),
        ('miscellaneous', 'Class 9 - Miscellaneous')
    ])
    item_classification_temperature = fields.Boolean(
        string="Temperature Sensitive")
    po_number_supplier = fields.Char(string="Suplier Po No.",
                                     copy=True)
    
    picking_code = fields.Selection(related='picking_id.picking_type_id.code',
        string="Picking Type Code", store=True)
    
    restrict_partner_id = fields.Many2one(
        'res.partner', 'Owner ', related='picking_id.customer_id',check_company=True,
        index='btree_not_null')


    def _get_customer_remaining_qty(self, product, customer_id, location_id):
        """Calculate what’s still in stock for this customer+location."""
        inc = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('restrict_partner_id', '=', customer_id),
            ('location_dest_id', '=', location_id),
            ('picking_type_id.code', '=', 'incoming'),
            ('state', '=', 'done'),
        ])
        total_in = sum(inc.mapped('product_uom_qty'))
        out = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('restrict_partner_id', '=', customer_id),
            ('location_id', '=', location_id),
            ('picking_type_id.code', '=', 'outgoing'),
            ('state', '=', 'done'),
        ])
        total_out = sum(out.mapped('product_uom_qty'))
        return max(0.0, total_in - total_out)
    
    
    remaining_qty = fields.Float(
        string="Quantity in Stock",
        compute="_compute_remaining_qty",
        store=True)
    
    @api.depends('product_id', 'restrict_partner_id', 'location_id')
    def _compute_remaining_qty(self):
        for move in self:
            if move.product_id and move.restrict_partner_id and move.location_id:
                move.remaining_qty = self._get_customer_remaining_qty(
                    move.product_id,
                    move.restrict_partner_id.id,
                    move.location_id.id,
                )
            else:
                move.remaining_qty = 0.0
    
    balance_qty = fields.Float(
        string="Balance Qty", 
        compute="_compute_balance_qty",
        store=True
        )
    
    @api.depends('remaining_qty', 'product_uom_qty')
    def _compute_balance_qty(self):
        for move in self:
            move.balance_qty = move.remaining_qty - move.product_uom_qty
            
    @api.onchange('product_id')
    def _auto_fill_description_picking(self):
        if self.picking_type_id.code == 'outgoing' and self.product_id:
            
            owner = self.picking_id.owner_id
            if not owner:
                self.description_picking = False
                return

            domain = [
                ('picking_id.picking_type_code', '=', 'incoming'),
                ('picking_id.state', '=', 'done'),
                ('product_id', '=', self.product_id.id),
                ('picking_id.owner_id', '=', owner.id)
            ]
            most_recent_incoming_move = self.env['stock.move'].search(
                domain,
                order='date desc',
                limit=1
            )
            if most_recent_incoming_move:
                self.description_picking = most_recent_incoming_move.description_picking
            else:
                self.description_picking = False
        else:
            return
        
    def _build_qr_payload(self, move_line=None):
        """Build QR code payload with warehouse information"""
        self.ensure_one()
        product_name = self.product_id.name or ""
        critical_flag = "Yes" if self.item_classification_critical else "No"
        danger_flag = f"Yes ({self.dangerous_goods_class})" if self.item_classification_dangerous else "No"
        temp_flag = "Yes" if self.item_classification_temperature else "No"
        unit_name = self.product_uom.name or ""
        inbound_name = self.picking_id.related_inbound_shipment.name or ""
        arrival_date = (self.picking_id.actual_date_of_arrival or "").strftime('%Y-%m-%d') if self.picking_id.actual_date_of_arrival else ""
        customer_name = self.restrict_partner_id.name or ""
        supplier_po = self.picking_id.supplier_po_number or ""
        customer_po = self.picking_id.receiving_waybill_number or ""
        file_number = self.picking_id.financial_id.code or ""
        
        location_name = ""
        warehouse_name = ""
        owner_name = ""
        quantity = ""
        
        if move_line:
            location_name = move_line.location_dest_id.name or ""
            warehouse_name = move_line.location_dest_id.warehouse_id.name or ""
            owner_name = move_line.owner_id.name or ""
            quantity = str(move_line.quantity or "")
            uom = move_line.product_uom_id.name
            weight = str(move_line.weight_per_item)
            length = str(move_line.length_mtr)
            width = str(move_line.width_mtr)
            height = str(move_line.height_mtr)
            area = str(move_line.area_m2)
            vol = str(move_line.volume_m3)
            value = str(move_line.item_value)
        
        lines = [
            f"Item Description: {product_name}",
            f"Critical Level: {critical_flag}",
            f"Temperature Sensitive: {temp_flag}",
            f"Dangerous?: {danger_flag}",
            f"Unit: {unit_name}",
            f"Related Inbound Shipment: {inbound_name}",
            f"Arrival Time: {arrival_date}",
            f"Customer: {customer_name}",
            f"Supplier PO Number: {supplier_po}",
            f"Customer PO Number: {customer_po}",
            f"Our File Number: {file_number}",
        ]
        
        if move_line:
            lines.extend([
                f"Location: {location_name}",
                f"Owner: {owner_name}",
                f"Quantity: {quantity}",
                f"Unit: {uom}",
                f"Weight(Kg): {weight}",
                f"Length(m): {length}",
                f"Width(m): {width}",
                f"Height(m): {height}",
                f"Area(m2): {area}",
                f"vol(m3): {vol}",
                f"Item Value(Naira): {value}",
                f"Warehouse: {warehouse_name}",
            ])
        
        return "\n".join(lines)
    
    def _create_qr_code(self, code):
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(code)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")
    
    def generate_qr_code(self): 
        self.ensure_one()
        payload = self._build_qr_payload()
        img = self._create_qr_code(payload)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        self.write({
            'qr_code': img_str,
        })
        
    def generate_location_specific_qr_code(self, move_line):
        """Generate QR code for a specific move line with location information"""
        self.ensure_one()
        payload = self._build_qr_payload(move_line)
        img = self._create_qr_code(payload)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
        
    def print_way_bill_item(self):
        self.is_label_printed = True 
        self.generate_qr_code()
        return self.env.ref('warehousing_system.print_waybill_item_report').report_action(self)

    def validate_dispatch_lines(self):
        if self.move_line_ids:
            for count, ml in enumerate(self.move_line_ids, 1):
                total_stock_availability_in_location = self.env['stock.quant'].sudo()._get_available_quantity(ml.product_id, ml.location_dest_id, allow_negative=False) # or 0.0
                if ml.quantity > total_stock_availability_in_location:
                    raise ValidationError(f"At line {count}: The quantity to dispatch is lesser than the amount remaining in the inventory location. The product {(ml.product_id.name)} available quantity is {total_stock_availability_in_location}")
        else:
            raise ValidationError("""
                                 This dispatch does not have any product / items 
                                 allocation during receipts""")

    @api.constrains('move_line_ids')
    def check_stock_allocation_quantity(self):
        for move in self:
            total_move_qty = sum(line.quantity for line in move.move_line_ids)
            if move.product_uom_qty < total_move_qty:
                raise ValidationError(_(
                    "Ops, you cannot proceed because the Allocated Store line total quantity "
                    "(%s) is greater than the quantity to receive (%s)."
                ) % (total_move_qty, move.product_uom_qty))
            
    #######################
    @api.onchange('product_id')
    def _onchange_product_id_set_remaining_qty(self):
        """Set remaining quantity when product is selected"""
        if self.product_id and self.restrict_partner_id and self.location_id:
            self.remaining_qty = self._get_customer_remaining_qty(
                self.product_id, 
                self.restrict_partner_id.id, 
                self.location_id.id
            )
        else:
            self.remaining_qty = 0
            
    def action_open_picking(self):
        """
        This method is called when the 'View Picking' button is clicked.
        It returns an action to open the form view of the associated stock.picking.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
            'target': 'current',
        }
        
    @api.onchange('product_uom')
    def _onchange_product_uom_update_lines(self):
        """
        When the UoM on the move changes, this method instantly updates the UoM
        on all existing move lines currently visible in the form.
        """
        if self.product_uom:
            for line in self.move_line_ids:
                line.product_uom_id = self.product_uom
            
            
            
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_label_printed = fields.Boolean(String="Label Printed")
    length_mtr = fields.Float(String="Length (m)", default=0.0)
    width_mtr = fields.Float(String="Width (m)", default=0.0)
    height_mtr = fields.Float(String="Height (m)", default=0.0)
    item_value = fields.Float(String="Item Value (Naira)", default=0.0)
    weight_per_item = fields.Float(String="Weight per item (Kg)", default=0.0)
    
    #Space occupied in m2
    area_m2 = fields.Float(String="Space occupied (m2)",
                           compute="_compute_stockmove_measure",
                           store=True
    )

    @api.depends('length_mtr', 'height_mtr', 'width_mtr')
    def _compute_stockmove_measure(self):
        for rec in self:
            rec.area_m2 = rec.length_mtr * rec.width_mtr
            rec.volume_m3 = rec.length_mtr * rec.width_mtr * rec.height_mtr
                
    #Space Occupied in m3
    volume_m3 = fields.Float(String="Space occupied (m3)", compute="_compute_stockmove_measure", store=True)
    area_chargeable = fields.Float(String="Chargeable Space(m2)")
    
    picking_code = fields.Selection(related='picking_id.picking_type_id.code',
        string="Picking Type Code", store=True)
    
    @api.onchange('quant_id')
    def _onchange_quant_id_fill_details(self):
        """
        When a Quant is selected on a dispatch line, this finds the
        original incoming line for that product/location/owner and copies its dimension details.
        """
        
        if self.picking_id.picking_type_id.code == 'outgoing' and self.quant_id:
            
            _logger.info(f"Quant selected: {self.quant_id.id}, Product: {self.quant_id.product_id.name}, Location: {self.quant_id.location_id.name}")
            
            product_id = self.quant_id.product_id.id
            location_id = self.quant_id.location_id.id
            owner_id = self.quant_id.owner_id.id if self.quant_id.owner_id else False
            lot_id = self.quant_id.lot_id.id if self.quant_id.lot_id else False
            
            domain = [
                ('product_id', '=', product_id),
                ('location_dest_id', '=', location_id),
                ('picking_id.state', '=', 'done'),
                ('picking_id.picking_type_id.code', '=', 'incoming'),
            ]
            
            if owner_id:
                domain.append(('owner_id', '=', owner_id))
            
            if lot_id:
                domain.append(('lot_id', '=', lot_id))
            
            _logger.info(f"Search domain: {domain}")
            
            original_move_line = self.env['stock.move.line'].search(
                domain, 
                order='date desc', 
                limit=1
            )
            
            if original_move_line:
                _logger.info(f"Found original move line: {original_move_line.id}")
                self.length_mtr = original_move_line.length_mtr
                self.width_mtr = original_move_line.width_mtr
                self.height_mtr = original_move_line.height_mtr
                self.weight_per_item = original_move_line.weight_per_item
                self.item_value = original_move_line.item_value
                
            else:
                _logger.info("No original move line found, clearing fields")
                self.length_mtr = 0.0
                self.width_mtr = 0.0
                self.height_mtr = 0.0
                self.weight_per_item = 0.0
                self.item_value = 0.0
        else:
            return

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        context = dict(self.env.context)

        picking_code  = context.get('filter_picking_code')
        customer_id   = context.get('filter_customer_id')
        location_id   = context.get('filter_location_id')
        warehouse_id   = context.get('filter_warehouse_id')
        
        _logger.info(
            f"name_search triggered. Context received: "
            f"customer_id={customer_id}, location_id={location_id}, picking_code={picking_code}"
        )
        if picking_code != 'outgoing' or not customer_id or not location_id:
            return super().name_search(name, args, operator, limit)

        # domain = [
        #     ('owner_id',         '=', customer_id),
        #     ('quantity',         '>', 0),
        #     '|',('warehouse_id', '=', warehouse_id),
        #     ('location_id',      '=', location_id),
        # ]
        
        domain = [
            ('owner_id', '=', customer_id),
            ('quantity', '>', 0),
            ('location_id', 'child_of', location_id),
        ]
        
        _logger.info(f"Searching stock.quant with domain: {domain}")
        
        grouped = self.env['stock.quant'].read_group(
            domain, ['product_id','quantity'], ['product_id'], lazy=False,
        )
        product_map = {
            g['product_id'][0]: g['quantity'] for g in grouped
        }
        product_ids = list(product_map)
        if not product_ids:
            return []

        prod_domain = [('id','in', product_ids)]
        if name:
            prod_domain.append(('name', operator, name))
        prods = self.search(prod_domain + args, limit=limit)

        result = []
        for p in prods:
            avail = product_map.get(p.id, 0.0)
            if avail <= 0:
                continue
            disp = _("%s (Available: %.2f)") % (p.name, avail)
            result.append((p.id, disp))
        return result
    