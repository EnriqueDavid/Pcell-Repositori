# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductUoM(models.Model):
    _inherit = "uom.uom"

    sunat_code = fields.Selection(
        selection="_get_sunat_code", string="SUNAT Unit Code")

    @api.model
    def _get_sunat_code(self):
        return self.env['pe.datas'].get_selection("PE.TABLA06")
