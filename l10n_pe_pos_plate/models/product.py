from odoo import api, fields, models, tools, _

class ProductProduct(models.Model):
    _inherit = "product.product"

    require_plate = fields.Boolean("Require Plate", related="product_tmpl_id.require_plate")
