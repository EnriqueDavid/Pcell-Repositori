# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pe_invoice_journal_id = fields.Many2one(
        'account.journal', string='Sales Invoice Journal S', compute="_compute_pe_journal_id")
    pe_voucher_journal_id = fields.Many2one(
        'account.journal', string='Voucher Journal', compute="_compute_pe_journal_id")
    pe_auto_journal_select = fields.Boolean("Auto Select Journal")

    # @api.multi

    def _compute_pe_journal_id(self):
        for config_id in self:
            config_id.pe_invoice_journal_id = self.env['account.journal'].search([('id', 'in', config_id.invoice_journal_ids.ids),
                                                                                  ('pe_invoice_code', '=', '01')], limit=1).id
            config_id.pe_voucher_journal_id = self.env['account.journal'].search([('id', 'in', config_id.invoice_journal_ids.ids),
                                                                                  ('pe_invoice_code', '=', '03')], limit=1).id
