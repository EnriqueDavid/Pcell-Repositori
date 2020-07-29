# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = "pos.order"

    refund_order_id = fields.Many2one(
        'pos.order', string="POS for which this invoice is the credit")
    refund_invoice_id = fields.Many2one(
        'account.move', string="Invoice for which this invoice is the credit")

    def refund(self):
        res = super(PosOrder, self).refund()
        order_id = res.get("res_id", False)
        if not order_id:
            return res
        for order in self.browse(order_id):
            order.refund_order_id = self.id
            order.refund_invoice_id = self.account_move.id
        return res

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        if res.get('type') == 'out_refund':
            res['reversed_entry_id'] = self.refund_invoice_id.id
        return res
