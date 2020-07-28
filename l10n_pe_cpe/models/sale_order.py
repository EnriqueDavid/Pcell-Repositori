# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pe_license_plate = fields.Char("License Plate", readonly=True, states={
                                   'draft': [('readonly', False)]}, copy=False)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pe_license_plate = fields.Char("License Plate", readonly=True, states={
                                   'draft': [('readonly', False)]}, copy=False)

    @api.onchange('pe_license_plate')
    def onchange_pe_license_plate(self):
        for line in self.order_line:
            if line.product_id.require_plate:
                line.pe_license_plate = self.pe_license_plate

    def action_confirm(self):
        for order_id in self:
            order_id.pe_check_invoice()
        return super(SaleOrder, self).action_confirm()

    def pe_check_invoice(self):
        for line in self.order_line:
            if line.product_uom_qty == 0.0 or line.price_unit == 0.0:
                raise UserError(
                    "La cantidad o precio del producto %s debe ser mayor a 0.0" % line.name)
            if not line.tax_id and line.product_uom_qty > 0:
                raise UserError(
                    "Es Necesario definir por lo menos un impuesto para el pruducto %s" % line.name)
            if line.product_id.require_plate and not (line.pe_license_plate or self.pe_license_plate):
                raise UserError(
                    "Es Necesario registrar el numero de placa para el pruducto %s" % line.name)
        partner_id = self.partner_id or self.partner_id.parent_id
        amount = self.company_id.sunat_amount or 0
        if self.amount_total >= amount and ((partner_id.vat == '0' or not partner_id.doc_type)):
            raise UserError("El dato ingresado no cumple con el estandar \nCuando el monto total a pagar, en la boleta de venta supere los S/ 700, será necesario consignar los siguientes datos del adquirente o usuario: * Apellidos y nombres.")
        if partner_id.l10n_latam_identification_type_id and not partner_id.vat:
            raise UserError(
                " El numero de documento de identidad de {} es requerido ".format(partner_id.name))
        if not partner_id.l10n_latam_identification_type_id and partner_id.vat:
            raise UserError(
                " El tipo de documento de identidad de %s es requerido " % partner_id.name)
        if partner_id.l10n_latam_identification_type_id == '6':
            is_valid = partner_id.validate_ruc(partner_id.doc_number)
            if not is_valid:
                raise UserError(" El ruc no es valido %s" % (partner_id.name))
            if partner_id.state != 'ACTIVO' or partner_id.condition != 'HABIDO':
                partner_id.with_context(force_update=1)._doc_number_change()
                if partner_id.state != 'ACTIVO' or partner_id.condition != 'HABIDO':
                    raise UserError(
                        " El cliente %s no tiene condicion de ACTIVO/HABIDO" % (partner_id.name))
