# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    internal_number = fields.Char("Internal Number", readonly=True, copy=False)
    debit_invoice_id = fields.Many2one(
        'account.move', string="Invoice for which this invoice is the debit")
    pe_related_ids = fields.Many2many(
        "account.move", string="Related Invoices", compute="_get_related_ids")

    def get_pe_data_by_code(self, table_code, code):
        self.ensure_one()
        return self.env['pe.datas'].search([('table_code', '=', table_code), ('code', '=', code)], limit=1)

    @api.depends('invoice_line_ids')
    def _get_related_ids(self):
        for move_id in self:
            related_ids = move_id.invoice_line_ids.mapped(
                'pe_invoice_id').ids or []
            if move_id.debit_origin_id:
                related_ids.append(move_id.debit_origin_id.id)
            if move_id.reversed_entry_id:
                related_ids.append(move_id.reversed_entry_id.id)
            move_id.pe_related_ids = related_ids

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        res = super(AccountMove, self)._prepare_refund(invoice, date_invoice=date_invoice, date=date,
                                                       description=description, journal_id=journal_id)
        journal_id = res.get('journal_id')
        if journal_id and not self.env.context.get("is_pe_debit_note"):
            journal = self.env['account.journal'].browse(journal_id)
            res['journal_id'] = journal.credit_note_id and journal.credit_note_id.id or journal.id
        elif journal_id and self.env.context.get("is_pe_debit_note"):
            journal = self.env['account.journal'].browse(journal_id)
            res['journal_id'] = journal.dedit_note_id and journal.dedit_note_id.id or journal.id
            res['type'] = "out_invoice"
            # res['debit_invoice_id']=invoice.id
            res['refund_invoice_id'] = invoice.id
        return res

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move_id in self:
            move_id.internal_number = move_id.name
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    amount_discount = fields.Float(
        "Amount Discount", compute="_compute_amount_discount")
    pe_invoice_ids = fields.Many2many('account.move', 'pe_account_invoice_line_invoice_rel',
                                      'line_id', 'move_id', string="Invoices lines", copy=False, readonly=True)
    pe_invoice_id = fields.Many2one(
        'account.move', string="Invoices", copy=False, readonly=True)
    #pe_amount_discount_included = fields.Float("Amount Discount Included", compute = "_compute_amount_discount")

    @api.depends('price_unit', 'discount', 'move_id.currency_id')
    def _compute_amount_discount(self):
        for line in self:
            price = line.price_unit * (line.discount or 0.0) / 100.0
            amount_discount = line.tax_ids.compute_all(price, line.move_id.currency_id,
                                                       line.quantity, line.product_id, line.move_id.partner_id)
            line.amount_discount = amount_discount['total_excluded']
            #line.pe_amount_discount_included = amount_discount['total_included']

    def set_pe_affectation_code(self):
        return True
