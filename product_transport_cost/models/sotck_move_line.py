# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    
    unit_cost_cargo = fields.Float("Cost. Un. Flete", digits=(16,4), related="move_id.purchase_line_id.unit_cost_cargo")