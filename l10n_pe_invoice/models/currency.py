# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class Currency(models.Model):
    _inherit = 'res.currency'

    pe_currency_code = fields.Selection(
        '_get_pe_invoice_code', "Currrency Code")

    @api.model
    def _get_pe_invoice_code(self):
        return self.env['pe.datas'].get_selection("PE.TABLA04")
