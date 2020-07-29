# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Pertner(models.Model):
    _inherit = "res.partner"

    pe_branch_code = fields.Char('Branch code')
