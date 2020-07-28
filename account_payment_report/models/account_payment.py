# -*- coding: utf-8 -*-

from odoo import models, fields, api


class account_payment(models.Model):
    _inherit = "account.payment"

    payment_user_id = fields.Many2one('res.users', string='User', readonly=True, states={'draft': [('readonly', False)]}, 
                                      default=lambda self: self.env.user, copy=False)