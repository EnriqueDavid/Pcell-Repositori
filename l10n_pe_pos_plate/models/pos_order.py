# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PosOrder(models.Model):
    _inherit = "pos.order"

    pe_license_plate = fields.Char("License Plate", size=10)

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()
        res['pe_license_plate'] = self.pe_license_plate
        return res
        
    def _action_create_invoice_line(self, line=False, move_id=False):
        line_id = super(PosOrder, self)._action_create_invoice_line(line, move_id)
        if line.pe_license_plate:
            line_id.sudo().pe_license_plate = line.pe_license_plate
        return line_id

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    pe_license_plate = fields.Char("License Plate", size=10)
