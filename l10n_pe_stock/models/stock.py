# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Picking(models.Model):
    _inherit = "stock.picking"

    pe_invoice_ids = fields.Many2many(comodel_name="stock.picking", string="Pickings", 
                                    compute ="_compute_pe_invoice_ids", readonly=True)
    pe_invoice_name = fields.Char("Internal Number", compute ="_compute_pe_invoice_ids")
    
    pe_type_operation = fields.Selection("_get_pe_type_operation", "Tipo de operación", 
                                         help="Tipo de operación efectuada", copy=False)
    pe_number = fields.Char("Numero de Guia")
    
    @api.model
    def _get_pe_type_operation(self):
        return self.env['pe.datas'].get_selection("PE.TABLA12")    
    
    @api.model
    def _compute_pe_invoice_ids(self):
        pe_invoice_ids = False
        pe_invoice_name=[]
        for stock_id in self:
            stock_id.sale_id
            pe_invoice_ids = stock_id.sale_id.order_line.invoice_lines.move_id.filtered(lambda r: r.type in ('out_invoice', 'out_refund'))
            if pe_invoice_ids:
                pe_invoice_name = pe_invoice_ids.mapped('name')
            stock_id.pe_invoice_ids=pe_invoice_ids and pe_invoice_ids.ids or []
            stock_id.pe_invoice_name = ", ".join(pe_invoice_name) or False

