# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    require_plate = fields.Boolean(
        'Require Plate', help="This Product Requires Vehicle License Plate")


class ProductCategory(models.Model):
    _inherit = "product.category"

    pe_unspsc_code = fields.Char("UNSPSC Code")
