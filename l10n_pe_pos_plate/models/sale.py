# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    ##@api.multi
    def prepare_pos_order(self):
        self.ensure_one()
        res = super(SaleOrder, self).prepare_pos_order()
        res['pe_license_plate'] = self.pe_license_plate
        return res

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ##@api.multi
    def prepare_pos_order_line(self):
        self.ensure_one()
        res = super(SaleOrderLine, self).prepare_pos_order_line()
        res['pe_license_plate'] = self.pe_license_plate
        return res