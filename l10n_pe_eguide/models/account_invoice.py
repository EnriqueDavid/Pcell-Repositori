# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    guide_number = fields.Char("Referral Guide", compute="_get_eguide_name")

    @api.model
    @api.depends("pe_stock_ids")
    def _get_eguide_name(self):
        for invoice in self:
            name = []
            for pe_stock_id in invoice.pe_stock_ids:
                if pe_stock_id.pe_guide_number and pe_stock_id.pe_guide_number != "/":
                    name.append(pe_stock_id.pe_guide_number)
            invoice.guide_number = ", ".join(name) or False

    @api.model
    def invoice_validate(self):
        despatch_numbers = {}
        for invoice in self:
            numbers = []
            for pe_stock_id in invoice.pe_stock_ids:
                if pe_stock_id.pe_guide_number and pe_stock_id.pe_guide_number != "/":
                    numbers.append(pe_stock_id.pe_guide_number)
            despatch_numbers[invoice.id] = numbers
        self = self.with_context(despatch_numbers=despatch_numbers)
        return super(AccountInvoice, self).invoice_validate()
