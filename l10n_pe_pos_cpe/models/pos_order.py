# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = "pos.order"

    pe_credit_note_code = fields.Selection(
        selection="_get_pe_crebit_note_type", string="Credit Note Code")
    #pe_is_refund = fields.Boolean("Is Refund")
    pe_invoice_type = fields.Selection(
        [("annul", "Annul"), ("refund", "Credit Note")], "Invoice Type")
    pe_motive = fields.Char("Reason for Credit Note")
    pe_license_plate = fields.Char("License Plate", size=10)
    pe_invoice_date = fields.Datetime("Invoice Date Time", copy=False)

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['pe_invoice_date'] = ui_order.get('pe_invoice_date', False)
        return res

    @api.model
    def _get_pe_crebit_note_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super(PosOrder, self)._onchange_partner_id()
        self.ensure_one()
        if self.partner_id and self.env.context.get('force_pe_journal'):
            partner_id = self.partner_id.parent_id or self.partner_id
            if partner_id.doc_type in ["6"]:
                journal_id = self.env['account.journal'].search([('company_id', '=', self.company_id.id),
                                                                 ('pe_invoice_code',
                                                                  '=', '01'),
                                                                 ('type', '=', 'sale')], limit=1)
                if journal_id:
                    self.invoice_journal = journal_id.id
            else:
                journal_id = self.env['account.journal'].search([('company_id', '=', self.company_id.id),
                                                                 ('pe_invoice_code',
                                                                  '=', '03'),
                                                                 ('type', '=', 'sale')], limit=1)
                self.invoice_journal = journal_id.id or self.partner_id.property_product_pricelist.id

    def refund(self):
        res = super(PosOrder, self).refund()
        order_id = res.get("res_id", False)
        if order_id:
            for order in self.browse([order_id]):
                order.pe_invoice_type = self.env.context.get(
                    "default_pe_invoice_type", False)
                if order.pe_invoice_type == 'annul' and order.refund_invoice_id:
                    if order.refund_invoice_id.state == 'posted':
                        order.invoice_journal = order.session_id.config_id.journal_id.id
                    else:
                        raise ValidationError(
                            _("You can not cancel the invoice, you must create a credit note"))
                else:
                    invoice_journal = self.invoice_journal.credit_note_id and self.invoice_journal.credit_note_id.id or self.invoice_journal.id
                    order.invoice_journal = invoice_journal or False
        return res

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        res['pe_credit_note_code'] = self.pe_credit_note_code or False
        res['pe_invoice_date'] = self.pe_invoice_date or False
        if self.pe_invoice_type == 'refund':
            res['ref'] = self.pe_motive or False
        res['invoice_line_ids'] = self._onchange_lines(res)
        return res

    def _onchange_lines(self, vals):
        move_new = self.env['account.move'].new(vals)
        move_new.invoice_line_ids.with_context(
            price_unit_pos=True)._onchange_product_id()
        invoice_lines = self._recompute_invoice_line(
            move_new.invoice_line_ids)
        return invoice_lines

    def _recompute_invoice_line(self, lines):
        res = []
        for line in lines:
            res += [(0, 0, self._prepare_invoice_cpe_line(line))]
        return res

    def _prepare_invoice_cpe_line(self, line):
        res = {
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'discount': line.discount,
            'price_unit': line.price_unit,
            'name': line.product_id.display_name,
            'tax_ids': [(6, 0, line.tax_ids.ids)],
            'product_uom_id': line.product_uom_id.id,
            'pe_affectation_code': line.pe_affectation_code,
        }
        return res

    def action_pos_order_invoice(self):
        for order in self:
            if order.pe_invoice_type == 'annul':
                raise ValidationError(
                    _("The invoice was canceled, you can not create a credit note"))
        return super(PosOrder, self).action_pos_order_invoice()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_price_unit(self):
        res = super()._get_computed_price_unit()
        if self._context.get("price_unit_pos") and self.price_unit:
            return self.price_unit
        return res
