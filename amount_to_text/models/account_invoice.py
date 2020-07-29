# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from . import amount_to_text_es

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    amount_text = fields.Char("Amount Text", compute="_get_amount_text")
    
    @api.depends('amount_total')
    def _get_amount_text(self):
        for invoice in self:
            if invoice.amount_total<2 and invoice.amount_total>=1:
                currency_name = invoice.currency_id.singular_name or invoice.currency_id.plural_name or invoice.currency_id.name or ""
            else:
                currency_name = invoice.currency_id.plural_name or invoice.currency_id.name or ""
            fraction_name = invoice.currency_id.fraction_name or ""
            amount_text = invoice.currency_id.amount_to_text(invoice.amount_total)
            invoice.amount_text= amount_text

