# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    unit_cost_cargo = fields.Float("Cost. Un. Flete", digits=(16,4))
    price_unit_cargo_cost = fields.Float("Costo Un. + Flete", digits=(16,4))
    tiene_has_refund = fields.Selection([('si','Si'),('no','No')], string="Tiene Retorno")

    @api.multi
    def get_transport_cost_by_order(self):
        self.ensure_one()
        src_location_ids = self.env['stock.location'].search([('usage','=','supplier'),('active','=',True)])
        dst_location_ids = self.env['stock.location'].search([('usage','=','internal'),('active','=',True)])
        product_ids = self._name == 'product.template' and self.product_variant_ids.ids or self.ids
        move_line_id = self.env['stock.move.line'].search([('location_id','in',src_location_ids.ids),
                                                            ('location_dest_id','in',dst_location_ids.ids),('state','=','done'),
                                                            ('product_id','in',product_ids),('move_id.purchase_line_id','!=',False)], order ="date desc", limit=1)
        if move_line_id:
            if move_line_id.move_id.purchase_line_id.unit_cost_cargo:
                self.unit_cost_cargo = move_line_id.move_id.purchase_line_id.unit_cost_cargo
                self.price_unit_cargo_cost = move_line_id.move_id.purchase_line_id.price_unit_cargo_cost
                if move_line_id.move_id.purchase_line_id.pe_has_refund:
                    self.tiene_has_refund = 'si'
                else:
                    self.tiene_has_refund = 'no'

class ProductProduct(models.Model):
    _inherit = "product.product"

    #unit_cost_cargo = fields.Float("Cost. Un. Flete", digits=(16,4))
    #price_unit_cargo_cost = fields.Float("Costo Un. + Flete", digits=(16,4))

    @api.multi
    def get_transport_cost_by_order(self):
        self.ensure_one()
        src_location_ids = self.env['stock.location'].search([('usage','=','supplier'),('active','=',True)])
        dst_location_ids = self.env['stock.location'].search([('usage','=','internal'),('active','=',True)])
        product_ids = self._name == 'product.template' and self.product_variant_ids.ids or self.ids
        move_line_id = self.env['stock.move.line'].search([('location_id','in',src_location_ids.ids),
                                                            ('location_dest_id','in',dst_location_ids.ids),('state','=','done'),
                                                            ('product_id','in',product_ids),('move_id.purchase_line_id','!=',False)], order ="date desc", limit=1)
        if move_line_id:
            if move_line_id.move_id.purchase_line_id.unit_cost_cargo:
                self.unit_cost_cargo = move_line_id.move_id.purchase_line_id.unit_cost_cargo
                self.price_unit_cargo_cost = move_line_id.move_id.purchase_line_id.price_unit_cargo_cost
                if move_line_id.move_id.purchase_line_id.pe_has_refund:
                    self.tiene_has_refund = 'si'
                else:
                    self.tiene_has_refund = 'no'
    