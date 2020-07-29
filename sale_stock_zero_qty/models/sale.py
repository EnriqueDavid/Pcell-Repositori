# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    filter_by_qty = fields.Boolean("Qty > 0", default=True)
    
    @api.onchange('filter_by_qty')
    def filter_by_qty_change(self):
        res = {}
        if self.filter_by_qty:
            res = {'domain': {'product_id':[('qty_available_daily','>',0)]}}
        else:
            res = {'domain': {'product_id':[]}}
        return res
        
#     @api.multi
#     @api.onchange('product_id')
#     def product_id_change(self):
#         res = super(SaleOrderLine, self).product_id_change()
#         #if self.order_id.filter_by_qty:
#         #    res['domain'].update({'product_id':})
#         return res