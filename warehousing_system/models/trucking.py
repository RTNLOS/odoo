from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class TruckingContact(models.Model):
    _inherit = 'res.partner'


    is_trucking_company = fields.Boolean(
        string="Is Trucking Company"
    )
    truck_reg_no = fields.Char(
        string="Truck Registration No."
    )


class WarehouseInventory(models.Model):
    _inherit = 'stock.picking'

    truck_company_name = fields.Many2one(
        'res.partner',
        string='Truck Company Name',
        domain=[('is_trucking_company', '=', True)],
    )
    
    truck_reg = fields.Char(
        string='Truck Registration No.',
        compute='_compute_truck_reg',
        inverse='_inverse_compute_truck_reg',
        store=True,
    )

    @api.depends('truck_company_name')
    def _compute_truck_reg(self):
        for rec in self:
            rec.truck_reg = rec.truck_company_name.truck_reg_no or False

    def _inverse_compute_truck_reg(self):
        for rec in self:
            if rec.truck_reg:
                partner = self.env['res.partner'].search([
                    ('truck_reg_no', '=', rec.truck_reg)
                ], limit=1)
                if partner:
                    rec.truck_company_name = partner.id