# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    #pe_debit_note_code = fields.Selection(selection="_get_pe_debit_note_type", string="Dedit Note Code")
    pe_credit_note_code = fields.Selection(
        selection="_get_pe_crebit_note_type", string="Credit Note Code")

    @api.model
    def _get_pe_crebit_note_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.model
    def _get_pe_debit_note_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG10")

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        journal_id = move.journal_id.credit_note_id.id or res.get('journal_id')
        journal = self.env['account.journal'].browse(journal_id)
        res.update({
            'journal_id': journal.id,
            'pe_credit_note_code': self.pe_credit_note_code,
            'pe_invoice_code': journal.pe_invoice_code,
        })
        return res

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        if self.env.context.get("is_pe_debit_note", False):
            invoice_domain = res['domain']
            if invoice_domain:
                del invoice_domain[0]
                res['domain'] = invoice_domain
        return res
