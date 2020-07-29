# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = "res.company"

    sunat_amount = fields.Float(string="Amount", digits=(16, 2), default=700)
