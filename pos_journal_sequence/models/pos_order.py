# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from dateutil.parser import parse as parse_date


class PosOrder(models.Model):
    _inherit = "pos.order"

    number = fields.Char(string='Number', readonly=True, copy=False)
    invoice_sequence_number = fields.Integer(
        string='Sequence of invoice numbers', readonly=True, copy=False)
    invoice_journal = fields.Many2one('account.journal', string='Sales invoice journal',   states={'draft': [('readonly', False)]}, readonly=True,
                                      domain="[('type', 'in', ['sale'])]", copy=True)
    date_invoice = fields.Date("Invoice Date")

    def _set_sequence(self):
        if self.invoice_journal and self.invoice_sequence_number:
            self.invoice_journal.sequence_id.pos_next(
                self.invoice_sequence_number+1)
        return self

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['to_invoice'] = True
        res['number'] = ui_order.get('number', False)
        res['invoice_journal'] = ui_order.get('invoice_journal', False)
        res['invoice_sequence_number'] = ui_order.get(
            'invoice_sequence_number', 0)
        res['date_invoice'] = parse_date(
            ui_order.get('date_invoice', '')).strftime(DATE_FORMAT)
        return res

    @api.model
    def _process_order(self, order, draft, existing_order):
        res = super()._process_order(order, draft, existing_order)
        if not res:
            return res
        order = self.browse(res)
        order._set_sequence()
        return res

    @api.model
    def create_from_ui(self, orders, draft=False):
        for i, order in enumerate(orders):
            if order.get('data', {}).get('invoice_journal') and not order.get('partial_payment'):
                orders[i]['to_invoice'] = True
        return super(PosOrder, self).create_from_ui(orders, draft=draft)

    def action_pos_order_invoice(self):
        res = super(PosOrder, self).action_pos_order_invoice()
        for order_id in self.filtered(lambda x: x.account_move):
            if not order_id.number:
                order_id.number = order_id.account_move.name
            order_id._set_sequence()
        return res

    def _prepare_invoice_vals(self):
        res = super()._prepare_invoice_vals()
        res.update({
            'invoice_date': self.date_invoice or self.date_order.date(),
            'name': self.number,
            'journal_id': (
                self.invoice_journal.id or
                self.session_id.config_id.invoice_journal_id.id),
        })
        return res
