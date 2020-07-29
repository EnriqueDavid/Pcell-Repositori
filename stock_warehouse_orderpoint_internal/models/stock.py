# -*- coding: utf-8 -*-
from odoo import models, fields

class Warehouse(models.Model):
    _inherit = "stock.warehouse"
    
    main_warehouse = fields.Boolean("it's main warehouse" )
