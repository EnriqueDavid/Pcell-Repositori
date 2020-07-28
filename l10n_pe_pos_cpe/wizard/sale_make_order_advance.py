# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePosOrder(models.TransientModel):
    _inherit = "sale.advance.pos.order"

    def _get_default_journal_id(self):
        active_id = self.env.context.get('active_id')
        journal_id = False
        if active_id:
            order_id = self.env['sale.order'].browse(active_id)
            if order_id.partner_id.doc_type in ["6"]:
                journal_id = self.env['account.journal'].search([('company_id', '=', order_id.company_id.id),
                                                                 ('pe_invoice_code',
                                                                  '=', '01'),
                                                                 ('type', '=', 'sale')], limit=1)
                if journal_id:
                    journal_id = journal_id
            else:
                journal_id = self.env['account.journal'].search([('company_id', '=', order_id.company_id.id),
                                                                 ('pe_invoice_code',
                                                                  '=', '03'),
                                                                 ('type', '=', 'sale')], limit=1)
                journal_id = journal_id or False
        return journal_id

    journal_id = fields.Many2one('account.journal', string='Journal',   required=True,
                                 domain="[('type', 'in', ['sale']),('pe_invoice_code','in',['01','03'])]",
                                 default=_get_default_journal_id)
    journal_ids = fields.Many2many(
        "account.journal", string="Invoice Sale Journals", domain="[('type', 'in', ['sale'])]")

    def create_orders(self):
        this = self.with_context(invoice_journal_id=self.journal_id.id)
        res = super(SaleAdvancePosOrder, this).create_orders()
        return res
