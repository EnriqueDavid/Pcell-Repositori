# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"
    
    pe_type_operation = fields.Selection("_get_pe_type_operation", "Tipo de operación", 
                                         help="Tipo de operación efectuada")
    pe_invoice_line_id = fields.Many2one('account.move.line', "Invoice Line")
    
    @api.model
    def _get_pe_type_operation(self):
        return self.env['pe.datas'].get_selection("PE.TABLA12")
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
     
    pe_unit_price = fields.Float('Price')
     