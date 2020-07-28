# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    auto_open_invoice = fields.Boolean("Auto Open Invoice")
    auto_done_stock = fields.Boolean("Auto Done Stock")