# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

class ProductTemplate(models.Model):
    _inherit = 'product.product'
    
    qty_available_daily =  fields.Float('Qty daily', digits=dp.get_precision('Product Unit of Measure'))
    
    @api.multi
    def get_qty_available_daily(self):
        product_ids = self.search([])
        for product_id in product_ids:
            product_id.qty_available_daily = product_id.qty_available