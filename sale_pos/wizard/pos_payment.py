# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def check(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')
        order = self.env['pos.order'].browse(active_id)
        session_id = order.session_id or self.env['pos.session'].search([
            ('state', '=', 'opened'),
            ('user_id', '=', self.env.uid)], limit=1)
        if not session_id:
            session_id = self.env['pos.session'].search([
                ('state', '=', 'opened')], limit=1)
        if not session_id and self.env.context.get("paid_on_line"):
            raise ValidationError(
                _("Payment can not be made. You need to create a new session"))
        elif order and self.env.context.get("paid_on_line"):
            order.write({'session_id': session_id.id})
        res = super(PosMakePayment, self).check()
        is_auto_open_invoice = all((
            self.env.context.get("paid_on_line"),
            self.config_id.auto_open_invoice, order.state == 'paid'))
        if is_auto_open_invoice:
            order.action_pos_order_invoice()
        return res
