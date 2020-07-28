# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductCategory(models.Model):
    _inherit = "product.category"

    pe_code = fields.Selection("_get_pe_code", "Código del catálogo", default="9", 
                               help="Código del catálogo utilizado. Sólo se podrá incluir las opciones 3 y 9 de la tabla 13.")
    pe_type = fields.Selection("_get_pe_type", "Tipo de existencia")
    
    @api.model
    def _get_pe_code(self):
        return self.env['pe.datas'].get_selection("PE.TABLA13")
    
    @api.model
    def _get_pe_type(self):
        return self.env['pe.datas'].get_selection("PE.TABLA05")
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    pe_code_osce = fields.Char('Código existencia OSCE')
    pe_price = fields.Float('Price product')
    
