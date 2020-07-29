# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from pdf417gen.encoding import to_bytes, encode_high, encode_rows
from pdf417gen.util import chunks
from pdf417gen.compaction import compact_bytes
from pdf417gen import render_image
import tempfile
from base64 import encodestring
import re
from datetime import datetime, date, timedelta
from odoo.tools.misc import formatLang
from io import StringIO, BytesIO
try:
    import qrcode
    qr_mod = True
except:
    qr_mod = False
from ast import literal_eval
import socket
from binascii import hexlify
from functools import partial


TYPE2JOURNAL = {
    'out_invoice': 'sale',  'in_invoice': 'purchase',
    'out_refund': 'sale',  'in_refund': 'purchase'}


class AccountMove(models.Model):
    _inherit = 'account.move'

    pe_additional_total_ids = fields.One2many(
        "account.move.additional.total", "invoice_id",
        string="Additional Monetary", readonly=True,
        states={'draft': [('readonly', False)]}, copy=False)
    pe_additional_property_ids = fields.One2many(
        "account.move.additional.property", "invoice_id",
        string="Additional Property", readonly=True,
        states={'draft': [('readonly', False)]}, copy=False)
    pe_taxable_amount = fields.Monetary(
        "Taxable Operations", compute="_pe_compute_operations")
    pe_exonerated_amount = fields.Monetary(
        "Exonerated Operations", compute="_pe_compute_operations")
    pe_unaffected_amount = fields.Monetary(
        "Unaffected Operations", compute="_pe_compute_operations")
    pe_free_amount = fields.Monetary(
        "Free Operations", compute="_pe_compute_operations")
    pe_cpe_id = fields.Many2one(
        "pe.cpe", "SUNAT CPE", states={'draft': [('readonly', False)]}, copy=False)
    pe_digest = fields.Char("Digest", related="pe_cpe_id.digest")
    pe_signature = fields.Text("Signature", related="pe_cpe_id.signature")
    pe_response = fields.Char("Response", related="pe_cpe_id.response")
    pe_note = fields.Text("Sunat Note", related="pe_cpe_id.note")
    pe_error_code = fields.Selection(
        "_get_pe_error_code", string="Error Code", related="pe_cpe_id.error_code", readonly=True)
    is_cpe = fields.Boolean("Is CPE", related="journal_id.is_cpe")
    pe_invoice_code = fields.Selection(selection="_get_pe_invoice_code", string="Invoice Type Code",
                                       related="journal_id.pe_invoice_code")
    pe_voided_id = fields.Many2one("pe.cpe", "Voided Document", states={
                                   'cancel': [('readonly', False)]}, copy=False)
    pe_summary_id = fields.Many2one("pe.cpe", "Summary Document", states={
                                    'cancel': [('readonly', False)]}, copy=False)
    pe_doc_name = fields.Char(
        "Document Name", compute="_get_peruvian_doc_name")
    sunat_pdf417_code = fields.Binary(
        "Pdf 417 Code", compute="_get_pdf417_code")
    pe_invoice_state = fields.Selection([
        ('draft', 'Draft'),
        ('generate', 'Generated'),
        ('send', 'Send'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Voucher Status', related="pe_cpe_id.state", copy=False)
    pe_debit_note_code = fields.Selection(selection="_get_pe_debit_note_type", string="Dedit Note Code",
                                          states={'draft': [('readonly', False)]})
    pe_credit_note_code = fields.Selection(selection="_get_pe_credit_note_type", string="Credit Note Code",
                                           states={'draft': [('readonly', False)]})
    origin_doc_code = fields.Selection("_get_origin_doc_code", "Origin Document Code", states={
                                       'draft': [('readonly', False)]}, compute="_compute_origin_doc")
    origin_doc_number = fields.Char("Origin Document Number", states={
                                    'draft': [('readonly', False)]}, compute="_compute_origin_doc")
    pe_additional_type = fields.Selection(
        "_get_pe_additional_document", string="Additional Document",
        readonly=True, states={'draft': [('readonly', False)]})
    pe_additional_number = fields.Char(string="Additional Number", readonly=True, states={
                                       'draft': [('readonly', False)]})
    pe_export_amount = fields.Monetary(
        "Export Amount", compute="_pe_compute_operations")
    pe_sunat_transaction = fields.Selection(
        "_get_pe_pe_sunat_transaction", string="SUNAT Transaction",
        readonly=True, states={'draft': [('readonly', False)]})
    pe_invoice_date = fields.Datetime("Invoice Date Time", copy=False)
    sunat_qr_code = fields.Binary("QR Code", compute="_compute_get_qr_code")
    pe_amount_tax = fields.Monetary(
        "Amount Tax", compute="_pe_compute_operations")
    pe_license_plate = fields.Char("License Plate", size=10, readonly=True, states={
                                   'draft': [('readonly', False)]}, copy=False)
    pe_condition_code = fields.Selection(
        "_get_pe_condition_code", "Condition Code", copy=False)
    pe_sunat_transaction51 = fields.Selection(
        "_get_pe_sunat_transaction51", string="Sunat Transaction Type",
        readonly=True, states={'draft': [('readonly', False)]})
    pe_total_discount = fields.Float(
        "Total Discount", compute="_compute_discount")
    pe_amount_discount = fields.Monetary(
        string='Discount', compute='_compute_discount',
        track_visibility='always')
    pe_total_discount_tax = fields.Monetary(
        string='Discount Tax', compute='_compute_discount', track_visibility='always')
    pe_charge_total = fields.Monetary(
        "Charge Amount", compute="get_pe_charge_amount",
        currency_field='company_currency_id')
    pe_icbper_amount = fields.Float(
        "ICBPER", compute="_compute_pe_icbper_amount", digits=(16, 2))

    @api.model
    def _compute_pe_icbper_amount(self):
        for invoice_id in self:
            pe_icbper_amount = 0.0
            for line in invoice_id.invoice_line_ids:
                pe_icbper_amount += invoice_id.currency_id.round(
                    line.pe_icbper_amount)
            invoice_id.pe_icbper_amount = pe_icbper_amount

    @api.model
    def get_pe_charge_amount(self):
        for invoice_id in self:
            pe_charge_total = 0.0
            for line in invoice_id.invoice_line_ids:
                pe_charge_total += line.pe_charge_amount
            invoice_id.pe_charge_total = pe_charge_total
    # @api.onchange('pe_sunat_transaction51')
    # def onchange_pe_sunat_transaction51(self):
    #    if self.pe_sunat_transaction51:
    #        self.pe_sunat_transaction = self.pe_sunat_transaction51[2:]

    @api.model
    def _get_pe_sunat_transaction51(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG51")

    @api.model
    def _get_pe_condition_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG19")

    @api.onchange('pe_license_plate')
    def onchange_pe_license_plate(self):
        for line in self.invoice_line_ids.filtered(lambda x: x.product_id and x.product_id.require_plate):
            line.pe_license_plate = self.pe_license_plate

    @api.onchange('invoice_date')
    def onchange_pe_license_plate(self):
        self.action_date_assign()

    @api.model
    def action_date_assign(self):
        for inv in self:
            today = fields.Date.context_today(self)
            if not inv.invoice_date:
                inv.pe_invoice_date = today
                continue
            local_date = fields.Date.from_string(today)
            dt = (
                local_date == fields.Date.from_string(inv.invoice_date)
                and today or str(inv.invoice_date) + ' 23:55:00')
            inv.pe_invoice_date = dt

    @api.model
    def _get_pe_pe_sunat_transaction(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG17")

    @api.model
    def _get_pe_additional_document(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG12")

    @api.depends('pe_related_ids')
    def _compute_origin_doc(self):
        for rec in self:
            inv = rec.pe_related_ids
            rec.origin_doc_number = inv and inv[0].name or False
            rec.origin_doc_code = inv and inv[0].pe_invoice_code or False

    @api.model
    def _get_origin_doc_code(self):
        return self.env['pe.datas'].get_selection("PE.TABLA10")

    @api.model
    def _get_pe_credit_note_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.model
    def _get_pe_debit_note_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG10")

    @api.depends('amount_total', 'currency_id', 'invoice_line_ids', 'invoice_line_ids.amount_discount')
    def _compute_discount(self):
        total_discount = 0.0
        ICPSudo = self.env['ir.config_parameter'].sudo()
        default_deposit_product_id = literal_eval(ICPSudo.get_param(
            'sale.default_deposit_product_id', default='False'))
        discount = 0.0
        total_discount_tax = 0.0
        for line in self.invoice_line_ids:
            if line.price_total < 0.0:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, self.currency_id, line.quantity, line.product_id, self.partner_id)
                if default_deposit_product_id and default_deposit_product_id != line.product_id.id:
                    if taxes:
                        for tax in taxes.get("taxes", []):
                            total_discount_tax += tax.get("amount", 0.0)
                    total_discount += line.price_total
                elif not default_deposit_product_id:
                    total_discount += line.price_total
                    if taxes:
                        for tax in taxes.get("taxes", []):
                            total_discount_tax += tax.get("amount", 0.0)

            discount += line.amount_discount
        self.pe_total_discount = abs(total_discount)
        self.pe_total_discount_tax = abs(total_discount_tax)
        self.pe_amount_discount = discount  # + total_discount

    @api.depends("pe_invoice_code")
    def _get_peruvian_doc_name(self):
        for invoice_id in self:
            if invoice_id.pe_invoice_code:
                doc = self.env['pe.datas'].search([('table_code', '=', 'PE.CPE.CATALOG1'),
                                                   ('code', '=', invoice_id.pe_invoice_code)])
                pe_doc_name = doc.name and doc.name+" Electronica" or ""
                print(pe_doc_name)
                invoice_id.pe_doc_name = pe_doc_name.title()
            print(pe_doc_name)

    def _get_pdf417_code(self):
        for invoice_id in self:
            res = []
            if invoice_id.name and invoice_id.journal_id.is_cpe:
                res.append(invoice_id.company_id.partner_id.doc_number)
                res.append(invoice_id.journal_id.pe_invoice_code or '')
                res.append(invoice_id.name.split("-")[0] or '')
                res.append(invoice_id.name.split("-")[1] or '')
                res.append(str(invoice_id.amount_tax))
                res.append(str(invoice_id.amount_total))
                res.append(str(invoice_id.invoice_date))
                res.append(invoice_id.partner_id.doc_type or "-")
                res.append(invoice_id.partner_id.doc_number or "-")
                res.append(invoice_id.pe_digest or "")
                res.append(invoice_id.pe_signature or "")
                res.append("")
                pdf417_string = '|'.join(res)
                data_bytes = compact_bytes(to_bytes(pdf417_string, 'utf-8'))
                code_words = encode_high(data_bytes, 10, 5)
                rows = list(chunks(code_words, 10))
                codes = list(encode_rows(rows, 10, 5))

                image = render_image(codes, scale=2, ratio=2, padding=7)
                # tmpf = tempfile.TemporaryFile(mode="r+")
                tmpf = BytesIO()
                image.save(tmpf, 'png')
                # tmpf.seek(0)
                invoice_id.sunat_pdf417_code = encodestring(tmpf.getvalue())

    @api.depends(
        'name', 'journal_id.is_cpe', 'journal_id.pe_invoice_code',
        'amount_tax', 'amount_total', 'invoice_date',
        'partner_id.doc_number', 'partner_id.doc_type',
        'company_id.partner_id.doc_number')
    def _compute_get_qr_code(self):
        for invoice in self:
            if not all((invoice.name != '/', invoice.journal_id.is_cpe, qr_mod)):
                invoice.sunat_qr_code = ""
                continue
            res = [
                invoice.company_id.partner_id.doc_number or "-",
                invoice.journal_id.pe_invoice_code or '',
                invoice.name.split("-")[0] or '',
                invoice.name.split("-")[1] or '',
                str(invoice.amount_tax), str(invoice.amount_total),
                fields.Date.to_string(
                    invoice.invoice_date), invoice.partner_id.doc_type or "-",
                invoice.partner_id.doc_number or "-", ""]
            qr_string = '|'.join(res)
            qr = qrcode.QRCode(
                version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
            qr.add_data(qr_string)
            qr.make(fit=True)
            image = qr.make_image()
            tmpf = BytesIO()
            image.save(tmpf, 'png')
            invoice.sunat_qr_code = encodestring(tmpf.getvalue())

    @api.model
    def _get_pe_invoice_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG1")

    def validate_sunat_invoice(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        sunat_url = ICPSudo.get_param('web.base.url').replace(
            'http://', '').replace('https://', '')
        sunat_server = socket.gethostbyname(sunat_url.split(':')[0])
        if self.pe_sunat_transaction51 and self.pe_sunat_transaction51[:2] == '02' and self.pe_invoice_code in ('01', ):
            for line in self.invoice_line_ids:
                if line.pe_affectation_code != '40':
                    raise UserError(
                        'El tipo de afectacion del producto %s debe ser Exportacion' % line.name)

        for line in self.invoice_line_ids:
            if line.quantity == 0.0 or line.price_unit == 0.0:
                raise UserError(
                    'La cantidad o precio del producto %s debe ser mayor a 0.0' % line.name)
            if not line.tax_ids and line.quantity > 0:
                raise UserError(
                    'Es Necesario definir por lo menos un impuesto para el pruducto %s' % line.name)
            if line.product_id.require_plate and not (line.pe_license_plate or self.pe_license_plate):
                raise UserError(
                    'Es Necesario registrar el numero de placa para el pruducto %s' % line.name)

        if not re.match('^(B|F){1}[A-Z0-9]{3}\\-\\d+$', self.name):
            raise UserError('El numero de la factura ingresada no cumple con el estandar.\nVerificar la secuencia del Diario por jemplo F001- o BN01-. \nPara cambiar ir a Configuracion/Contabilidad/Diarios/Secuencia del asiento')
        if self.partner_id.parent_id and self.partner_id.doc_number:
            raise UserError(
                'Para generar este comprobante debe cambiar los datos  de contacto {} \nPor los datos de la Empresa principal {}' .format(self.partner_id.name, self.partner_id.parent_id.name))
        if self.pe_invoice_code in ('03', ) or self.reversed_entry_id.pe_invoice_code in ('03', ):
            doc_type = self.partner_id.doc_type or '-'
            doc_number = self.partner_id.doc_number or '-'
            if doc_type == '6' and doc_number[:2] != '10':
                raise UserError('El dato ingresado no cumple con el estandar \nTipo: %s \nNumero de documento: %s\nDeberia emitir una Factura. Cambiar en Factura/Otra Informacion/Diario' % (
                    doc_type, doc_number))
            amount = self.company_id.sunat_amount or 0
            if self.amount_total >= amount and (doc_type == '0' or doc_number == '0'):
                raise UserError('El dato ingresado no cumple con el estandar \nTipo: %s \nNumero de documento: %s\nSon obligatorios el Tipo de Doc. y Numero' % (
                    doc_type, doc_number))

        if self.pe_invoice_code in ('01', ) or self.reversed_entry_id.pe_invoice_code in ('01', ):
            doc_type = self.partner_id.doc_type or self.partner_id.parent_id.doc_type or '-'
            doc_number = self.partner_id.doc_number or self.partner_id.parent_id.doc_number or '-'
            if doc_type not in ('6') or not doc_number:
                raise UserError(' El numero de documento de identidad del receptor debe ser RUC \nTipo: %s \nNumero de documento: %s' % (
                    doc_type, doc_number))
            if doc_type == '6':
                partner_id = self.partner_id or self.partner_id.parent_id
                is_valid = partner_id.validate_ruc(doc_number)
                if not is_valid:
                    raise UserError(' El ruc no es valido' %
                                    (doc_type, doc_number))
                if partner_id.state != 'ACTIVO' or partner_id.condition != 'HABIDO':
                    partner_id.with_context(
                        force_update=1)._doc_number_change()
                    if partner_id.state != 'ACTIVO' or partner_id.condition != 'HABIDO':
                        raise UserError(
                            ' El cliente no tiene condicion de ACTIVO/HABIDO %s %s' % (doc_type, doc_number))
        date_invoice = fields.Datetime.from_string(
            self.pe_invoice_date or self.invoice_date)
        today = fields.Datetime.context_timestamp(self, datetime.now())
        days = today.replace(tzinfo=None) - date_invoice
        if days.days > 6 and (self.pe_invoice_code in ('01', ) or self.reversed_entry_id.pe_invoice_code in ('01', )):
            raise UserError(
                'La fecha de emision no puede ser menor a 6 dias de hoy ni mayor a la fecha de hoy.')
        if days.days < 0:
            raise UserError(
                'La fecha de emision no puede ser menor a 6 dias de hoy ni mayor a la fecha de hoy.')
        company_id = self.company_id.partner_id

    def post(self):
        res = super(AccountMove, self).post()
        for invoice_id in self:
            invoice_id.internal_number = invoice_id.name
            invoice_id.action_date_assign()
            if invoice_id.is_cpe and invoice_id.journal_id.pe_invoice_code in ['01', '03', '07', '08']:
                invoice_id.validate_sunat_invoice()
                invoice_id._get_additionals()
                if not invoice_id.pe_cpe_id:
                    cpe_id = self.env['pe.cpe'].create_from_invoice(invoice_id)
                    invoice_id.pe_cpe_id = cpe_id.id
                else:
                    cpe_id = invoice_id.pe_cpe_id
                if invoice_id.journal_id.pe_invoice_code == "03" or invoice_id.origin_doc_code == "03":
                    if not invoice_id.pe_condition_code:
                        invoice_id.pe_condition_code = "1"
                    else:
                        invoice_id.pe_condition_code = "2"
                if invoice_id.company_id.pe_is_sync:
                    cpe_id.generate_cpe()
                    if invoice_id.journal_id.is_synchronous or invoice_id.journal_id.pe_invoice_code == "01" or invoice_id.origin_doc_code == "01":
                        if not self.env.context.get("is_pos_invoice"):
                            cpe_id.action_send()
                else:
                    cpe_id.generate_cpe()
                # if cpe_id.error_code and (int(cpe_id.error_code)>=100 and int(cpe_id.error_code)<=1999):
                #    raise UserError(_("The invoice was canceled due to:\n Error Code %s \n%s") % (cpe_id.error_code, cpe_id.note))
                # if cpe_id.error_code and (int(cpe_id.error_code)>=2000 and int(cpe_id.error_code)<=3999):
                #    invoice_id.action_invoice_cancel()
                if (invoice_id.journal_id.pe_invoice_code in ["07", "08"] and invoice_id.origin_doc_code == "03") or invoice_id.journal_id.pe_invoice_code == "03":
                    if invoice_id.journal_id.is_homologation or not invoice_id.journal_id.is_synchronous:
                        pe_summary_id = self.env['pe.cpe'].get_cpe_async(
                            "rc", invoice_id)
                        invoice_id.pe_summary_id = pe_summary_id.id
        return res

    @api.model
    def _get_pe_error_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

    @api.depends("currency_id", "partner_id", "invoice_line_ids", "invoice_line_ids.tax_ids",
                 "invoice_line_ids.quantity", "invoice_line_ids.product_id", "invoice_line_ids.discount")
    def _pe_compute_operations(self):
        for invoice_id in self:
            total_1001 = 0
            total_1002 = 0
            total_1003 = 0
            total_1004 = 0
            pe_export_amount = 0
            pe_tax_amount = 0.0
            round_curr = invoice_id.currency_id.round
            for line in invoice_id.invoice_line_ids:
                price_unit = line.price_unit * \
                    (1 - (line.discount or 0.0) / 100.0)
                total_excluded = line.tax_ids.compute_all(
                    price_unit, invoice_id.currency_id, line.quantity, line.product_id, invoice_id.partner_id)['total_excluded']
                if line.pe_affectation_code == '10':
                    total_1001 += total_excluded
                elif line.pe_affectation_code == '20':
                    total_1002 += total_excluded
                elif line.pe_affectation_code == '30':
                    total_1003 += total_excluded
                elif line.pe_affectation_code == '40':
                    pe_export_amount += total_excluded
                else:
                    price_unit = line.price_unit
                    total_excluded = line.tax_ids.compute_all(
                        price_unit, invoice_id.currency_id, line.quantity, line.product_id, invoice_id.partner_id)['total_excluded']
                    total_1004 += total_excluded
            invoice_id.pe_taxable_amount = invoice_id.currency_id.round(
                total_1001)
            invoice_id.pe_exonerated_amount = invoice_id.currency_id.round(
                total_1002)
            invoice_id.pe_unaffected_amount = invoice_id.currency_id.round(
                total_1003)
            invoice_id.pe_free_amount = total_1004
            invoice_id.pe_export_amount = invoice_id.currency_id.round(
                pe_export_amount)
            # pe_amount_tax = sum((round_curr(line.amount_total) for line in invoice_id.tax_line_ids.filtered(lambda tax: tax.tax_id.pe_tax_type.code in ('1000', '2000', '9999'))))  original
            pe_amount_tax = sum((round_curr(line.price_total) for line in invoice_id.line_ids.filtered(
                lambda tax: tax.tax_line_id.l10n_pe_edi_tax_code in ('1000', '1016', '2000', '9999'))))  # add fre
            invoice_id.pe_amount_tax = pe_amount_tax - invoice_id.pe_charge_total

    @api.depends('currency_id')
    def _get_additionals(self):
        self.ensure_one()
        for total in self.pe_additional_total_ids:
            total.unlink()
        for property in self.pe_additional_property_ids:
            property.unlink()
        amount_total = self.pe_taxable_amount + self.pe_exonerated_amount + \
            self.pe_unaffected_amount + self.pe_export_amount + self.amount_tax
        if amount_total > 0 and self.journal_id.pe_invoice_code in ('01', '03'):
            amount_text = self.currency_id.amount_to_text(amount_total)
            self.env['account.move.additional.property'].create(
                {'code': '1000', 'value': amount_text, 'invoice_id': self.id})
        total_1001 = {
            'code': '1001', 'total_amount': self.pe_taxable_amount, 'invoice_id': self.id}
        total_1002 = {
            'code': '1002', 'total_amount': self.pe_exonerated_amount, 'invoice_id': self.id}
        total_1003 = {'code': '1003', 'total_amount': self.pe_unaffected_amount +
                      self.pe_export_amount, 'invoice_id': self.id}
        total_1004 = {'code': '1004',
                      'total_amount': self.pe_free_amount, 'invoice_id': self.id}
        self.env['account.move.additional.total'].create(total_1001)
        self.env['account.move.additional.total'].create(total_1002)
        self.env['account.move.additional.total'].create(total_1003)
        if self.pe_free_amount > 0:
            self.env['account.move.additional.total'].create(total_1004)
            self.env['account.move.additional.property'].create(
                {'code': '1002', 'value': 'TRANSFERENCIA GRATUITA', 'invoice_id': self.id})
        igv = self.invoice_line_ids.mapped('tax_ids').filtered(
            lambda tax: tax.l10n_pe_edi_tax_code == '1000')
        company_id = self.company_id.partner_id
        if not igv:
            line_ids = self.invoice_line_ids.filtered(
                lambda line: line.product_id.type in ('consu', 'product'))
            if (self.invoice_line_ids.filtered(lambda line: line.product_id == False)) and line_ids and self.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9997'):
                self.env['account.move.additional.property'].create({'code': '2001', 'value': 'BIENES TRANSFERIDOS EN LA AMAZONÍA REGIÓN SELVA PARA SER CONSUMIDOS EN LA MISMA',
                                                                     'invoice_id': self.id})
            line_ids = self.invoice_line_ids.filtered(
                lambda line: line.product_id.type in ('service', ))
            if line_ids and self.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9997'):
                self.env['account.move.additional.property'].create({'code': '2002', 'value': 'SERVICIOS TRANSFERIDOS EN LA AMAZONÍA REGIÓN SELVA PARA SER CONSUMIDOS EN LA MISMA',
                                                                     'invoice_id': self.id})
        total_discount = self.pe_total_discount - self.pe_total_discount_tax
        if total_discount > 0:
            total_2005 = {'code': '2005',
                          'total_amount': total_discount, 'invoice_id': self.id}
            self.env['account.move.additional.total'].create(total_2005)

    def button_cancel(self):
        res = super().button_cancel()
        if res:
            for invoice_id in self:
                if invoice_id.is_cpe and invoice_id.pe_cpe_id and invoice_id.pe_cpe_id.state not in ["draft", "cancel"]:
                    raise UserError(
                        "No puede cancelar este documento, esta enviado a la sunat")
        return res

    def button_annul(self):
        res = super().button_annul()
        if res:
            for invoice_id in self:
                if invoice_id.is_cpe and invoice_id.pe_cpe_id and invoice_id.pe_cpe_id.state not in ["draft", "cancel"]:
                    if invoice_id.journal_id.pe_invoice_code == "03" or invoice_id.origin_doc_code == "03":
                        invoice_id.pe_condition_code = "3"
                        if invoice_id.pe_summary_id.state == 'done':
                            pe_summary_id = self.env['pe.cpe'].get_cpe_async(
                                "rc", invoice_id, True)
                            invoice_id.pe_summary_id = pe_summary_id.id
                    else:
                        invoice_date = fields.Datetime.from_string(
                            invoice_id.pe_invoice_date or invoice_id.invoice_date)
                        today = fields.Datetime.context_timestamp(
                            self, datetime.now())
                        days = today.replace(tzinfo=None) - invoice_date
                        if days.days > 7:
                            raise UserError("No puede cancelar este documento, solo se puede hacer antes de las 72 horas "
                                            "contadas a partir del día siguiente de la fecha consignada en el CDR (constancia de recepción)."
                                            "\nPara cancelar este Documento emita una Nota de Credito")
                        # if invoice_id.pe_invoice_code in ['01', '03']:
                        voided_id = self.env['pe.cpe'].get_cpe_async(
                            'ra', invoice_id)
                        invoice_id.pe_voided_id = voided_id.id
        return res

    def button_draft(self):
        states = self.mapped('state')
        res = super().button_draft()
        if self.filtered(lambda inv: inv.pe_cpe_id and inv.pe_cpe_id.state in ['send', 'verify', 'done'] and 'cancel' not in states):
            raise UserError(
                "Este documento ha sido informado a la SUNAT no se puede cambiar a borrador")
        return res

    @api.model
    def pe_credit_debit_code(self, invoice_ids, credit_code, debit_code):
        for invoice in self.browse(invoice_ids):
            if credit_code:
                invoice.pe_credit_note_code = credit_code
            elif debit_code:
                invoice.pe_debit_note_code = debit_code

    def action_invoice_sent(self):
        res = super().action_invoice_sent()
        self.ensure_one()
        if self.journal_id.is_cpe and self.pe_cpe_id:
            template = self.env.ref(
                'l10n_pe_cpe.email_template_edi_invoice_cpe2', False)
            attach = {}
            attach['name'] = self.pe_cpe_id.datas_sign_fname
            attach['type'] = "binary"
            attach['datas'] = self.pe_cpe_id.datas_sign
            attach['res_model'] = "mail.compose.message"
            attachment_id = self.env['ir.attachment'].create(attach)
            attachment_ids = []
            attachment_ids.append(attachment_id.id)
            attach = {}
            result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
                'account.report_invoice').render_qweb_pdf(self.ids)
            attach['name'] = "%s.pdf" % self.pe_cpe_id.get_document_name()
            attach['type'] = "binary"
            attach['datas'] = encodestring(result_pdf)
            attach['res_model'] = "mail.compose.message"
            attachment_id = self.env['ir.attachment'].create(attach)
            attachment_ids.append(attachment_id.id)
            vals = {}
            vals['default_use_template'] = bool(template)
            vals['default_template_id'] = template and template.id or False
            vals['default_attachment_ids'] = [(6, 0, attachment_ids)]
            res['context'].update(vals)
        return res

    def get_public_cpe(self):
        self.ensure_one()
        res = {}
        if self.journal_id.is_cpe and self.pe_cpe_id:
            result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
                'account.report_invoice').render_qweb_pdf(self.ids)
            res['datas_sign'] = str(self.pe_cpe_id.datas_sign, "utf-8")
            res['datas_invoice'] = str(encodestring(result_pdf), "utf-8")
            res['name'] = self.pe_cpe_id.get_document_name()
        return res

    def action_send_mass_mail(self):
        today = fields.Date.context_today(self)
        invoice_ids = self.search([('state', 'not in', [
                                  'draft', 'cancel', 'annul']), ('invoice_date', '=', today), ('is_cpe', '=', True)])
        for invoice_id in invoice_ids:
            if invoice_id.partner_id.email:
                account_mail = invoice_id.action_invoice_sent()
                context = account_mail.get('context')
                if not context:
                    continue
                template_id = account_mail['context'].get(
                    'default_template_id')
                if not template_id:
                    continue
                attachment_ids = []
                if context.get('default_attachment_ids', False):
                    for attach in context.get('default_attachment_ids'):
                        attachment_ids += attach[2]
                mail_id = self.env['mail.template'].browse(template_id)
                mail_id.send_mail(invoice_id.id, force_send=True, email_values={
                                  'attachment_ids': attachment_ids})
                # vals={}
                # vals['model']= 'account.move'
                # vals['res_id']= invoice_id.id
                # vals['use_template']= True
                # vals['template_id']= template_id
                # vals['composition_mode']= context.get('composition_mode')
                # if context.get('default_attachment_ids', False):
                #    vals['attachment_ids']=context.get('default_attachment_ids', False)
                # mail_id = self.env['mail.compose.message'].with_context(**context).create(vals)
                # mail_id.send_mail_action()

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        journal_type = TYPE2JOURNAL.get(self.type)
        if not journal_type:
            return res
        journal = self.env['account.journal']
        if not all((self.partner_id, self.env.context.get('force_pe_journal'))):
            return res
        partner_id = self.partner_id.parent_id or self.partner_id
        doc_type = partner_id.doc_type
        if doc_type in ('6') and not self.env.context.get('is_pos_invoice') and self.journal_id.pe_invoice_code != '01':
            journal_id = journal.search([
                ('company_id', '=', self.company_id.id),
                ('pe_invoice_code', '=', '01'),
                ('type', '=', journal_type)], limit=1)
            if journal_id:
                self.journal_id = journal_id.id
            # if doc_type == '0':
            #     self.pe_sunat_transaction = '02'
            #     self.pe_sunat_transaction51 = '0102'
        else:
            if doc_type in ('6', ):
                journal_id = journal.search([
                    ('company_id', '=', self.company_id.id),
                    ('pe_invoice_code', '=', '01'),
                    ('type', '=', journal_type)], limit=1)
                if journal_id:
                    self.journal_id = journal_id.id
            else:
                if self.journal_id.pe_invoice_code != '03':
                    journal_id = journal.search([
                        ('company_id', '=', self.company_id.id),
                        ('pe_invoice_code', '=', '03'),
                        ('type', '=', journal_type)], limit=1)
                    if journal_id:
                        self.journal_id = journal_id.id
        return res

    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_group(self):
        ''' Helper to get the taxes grouped according their account.tax.group.
        This method is only used when printing the invoice.
        '''
        
        for move in self:
            res = {}
            currency = move.currency_id or move.company_id.currency_id
            lang_env = move.with_context(lang=move.partner_id.lang).env
            fmt = partial(formatLang, self.with_context(lang=move.partner_id.lang).env, currency_obj=currency)
            for line in move.line_ids:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_ids.compute_all(
                    price_reduce, quantity=line.quantity,
                    product=line.product_id, partner=move.partner_id)['taxes']
                for tax in line.tax_ids:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            move.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res), l[0].id
            ) for l in res]


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    pe_affectation_code = fields.Selection(
        selection="_get_pe_reason_code",
        string="Type of affectation",
        help="Type of affectation to the IGV")
    pe_affectation_code2 = fields.Integer(
        string="Typeafect",
        help="Type of affectation to the IGV", store=True)
    pe_tier_range = fields.Selection(
        selection="_get_pe_tier_range", string="Type of System",
        help="Type of system to the ISC")
    pe_license_plate = fields.Char("License Plate", size=10)
    pe_charge_amount = fields.Float(
        "Charge Amount", compute="get_pe_charge_amount")
    pe_icbper_amount = fields.Float(
        "ICBPER", compute="_compute_pe_icbper_amount")

    @api.depends("tax_ids")
    def _compute_pe_icbper_amount(self):
        for line in self:
            pe_icbper_amount = 0.0
            if line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == "7152"):
                price_unit = line.price_unit * \
                    (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.with_context(round=False).compute_all(price_unit, line.move_id.currency_id, 1, line.product_id,
                                                                           line.move_id.partner_id).get("taxes", [])
                for tax_val in taxes:
                    tax = self.env['account.tax'].browse(tax_val.get('id'))
                    if tax.l10n_pe_edi_tax_code == "7152":
                        pe_icbper_amount += tax_val.get('amount', 0.0)
            line.pe_icbper_amount = pe_icbper_amount

    @api.depends('price_unit', 'tax_ids', 'discount')
    def get_pe_charge_amount(self):
        for line in self:
            pe_charge_amount = 0.0
            if line.tax_ids.filtered(lambda tax: tax.pe_is_charge == True):
                price_unit = line.price_unit * \
                    (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.with_context(round=False).compute_all(price_unit, line.move_id.currency_id, 1, line.product_id,
                                                                           line.move_id.partner_id).get("taxes", [])
                for tax_val in taxes:
                    tax = self.env['account.tax'].browse(tax_val.get('id'))
                    if tax.pe_is_charge:
                        pe_charge_amount += tax_val.get('amount', 0.0)
            line.pe_charge_amount = pe_charge_amount

    @api.model
    def _get_pe_reason_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG7")

    @api.model
    def _get_pe_tier_range(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG8")

    def _set_free_tax(self):
        if self.pe_affectation_code not in ['10', '20', '30', '40']:
            ids = self.tax_ids.ids
            vat = self.env['account.tax'].search([
                ('l10n_pe_edi_tax_code', '=', '9996'),
                ('id', 'in', ids)])
            self.discount = 100
            if not vat:
                res = self.env['account.tax'].search([
                    ('l10n_pe_edi_tax_code', '=', '9996')], limit=1)
                self.tax_ids = [(6, 0, ids+res.ids)]
        else:
            if self.discount == 100:
                self.discount = 0
            ids = self.tax_ids.ids
            vat = self.env['account.tax'].search(
                [('l10n_pe_edi_tax_code', '=', '9996'), ('id', 'in', ids)])
            if vat:
                res = self.env['account.tax'].search(
                    [('id', 'in', ids), ('id', 'not in', vat.ids)]).ids
                self.tax_ids = [(6, 0, res)]

    @api.onchange('discount')
    def onchange_affectation_code_discount(self):
        for rec in self:
            if rec.discount != 100:
                continue
            rec.pe_affectation_code = '11'

    @api.onchange('pe_affectation_code')
    def onchange_pe_affectation_code(self):
        if self.move_id.type == 'out_invoice':
            if self.pe_affectation_code in ['10', '11', '12', '13', '14', '15', '16', '17']:
                ids = self.tax_ids.filtered(
                    lambda tax: tax.l10n_pe_edi_tax_code == '1000').ids
                res = self.env['account.tax'].search(
                    [('l10n_pe_edi_tax_code', '=', '1000'), ('id', 'in', ids)])
                if not res:
                    res = self.env['account.tax'].search(
                        [('l10n_pe_edi_tax_code', '=', '1000')], limit=1)
                self.tax_ids = [(6, 0, ids+res.ids)]
                self._set_free_tax()
            elif self.pe_affectation_code in ['20', '21']:
                ids = self.tax_ids.filtered(
                    lambda tax: tax.l10n_pe_edi_tax_code == '9997').ids
                res = self.env['account.tax'].search(
                    [('l10n_pe_edi_tax_code', '=', '9997'), ('id', 'in', ids)])
                if not res:
                    res = self.env['account.tax'].search(
                        [('l10n_pe_edi_tax_code', '=', '9997')], limit=1)
                self.tax_ids = [(6, 0, ids+res.ids)]
                self._set_free_tax()
            elif self.pe_affectation_code in ['30', '31', '32', '33', '34', '35', '36']:
                ids = self.tax_ids.filtered(
                    lambda tax: tax.l10n_pe_edi_tax_code == '9998').ids
                res = self.env['account.tax'].search(
                    [('l10n_pe_edi_tax_code', '=', '9998'), ('id', 'in', ids)])
                if not res:
                    res = self.env['account.tax'].search(
                        [('l10n_pe_edi_tax_code', '=', '9998')], limit=1)
                self.tax_ids = [(6, 0, ids+res.ids)]
                self._set_free_tax()
            elif self.pe_affectation_code in ['40']:
                ids = self.tax_ids.filtered(
                    lambda tax: tax.l10n_pe_edi_tax_code == '9995').ids
                res = self.env['account.tax'].search(
                    [('l10n_pe_edi_tax_code', '=', '9995'), ('id', 'in', ids)])
                if not res:
                    res = self.env['account.tax'].search(
                        [('l10n_pe_edi_tax_code', '=', '9995')], limit=1)
                self.tax_ids = [(6, 0, ids+res.ids)]
                self._set_free_tax()

    def set_pe_affectation_code(self):
        igv = self.tax_ids.filtered(
            lambda tax: tax.l10n_pe_edi_tax_code == '1000')
        if self.tax_ids and igv:
            if self.discount == 100:
                self.pe_affectation_code = '11'
                self._set_free_tax()
            else:
                self.pe_affectation_code = '10'
        vat = self.tax_ids.filtered(
            lambda tax: tax.l10n_pe_edi_tax_code == '9997')
        if self.tax_ids and vat:
            if self.discount == 100:
                self.pe_affectation_code = '21'
                self._set_free_tax()
            else:
                self.pe_affectation_code = '20'
        vat = self.tax_ids.filtered(
            lambda tax: tax.l10n_pe_edi_tax_code == '9998')
        if self.tax_ids and vat:
            if self.discount == 100:
                self.pe_affectation_code = '31'
                self._set_free_tax()
            else:
                self.pe_affectation_code = '30'
        vat = self.tax_ids.filtered(
            lambda tax: tax.l10n_pe_edi_tax_code == '9995')
        if self.tax_ids and vat:
            self.pe_affectation_code = '40'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        for rec in self.filtered(lambda x: x.product_id):
            rec.set_pe_affectation_code()
        self = self.with_context(check_move_validity=False)
        return res

    def get_price_unit(self, all=False):
        self.ensure_one()
        price_unit = self.price_unit
        if all:
            price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            tax_ids = self.tax_ids
        else:
            tax_ids = self.tax_ids.filtered(
                lambda tax: tax.l10n_pe_edi_tax_code != '9996')
        res = tax_ids.with_context(round=False).compute_all(
            price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
        return res


class AccountAdditionalTotal(models.Model):
    _name = 'account.move.additional.total'
    _description = "Additional Monetary Total"
    _order = 'code'

    code = fields.Selection("_get_code", "Code")
    name = fields.Char("Name")
    invoice_id = fields.Many2one(
        "account.move", string="Invoice", ondelete='cascade', index=True)
    reference_amount = fields.Float(string="Reference Amount")
    payable_amount = fields.Float(string="Payable Amount")
    percent = fields.Float(string="Percent", digits='Discount')
    total_amount = fields.Float(string="Total Amount")

    @api.model
    def _get_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG14")


class AccountAdditionalProperty(models.Model):
    _name = 'account.move.additional.property'
    _description = "Additional Property"
    _order = 'code'

    code = fields.Selection("_get_code", "Code")
    name = fields.Char("Name")
    value = fields.Char("Value")
    invoice_id = fields.Many2one(
        comodel_name="account.move", string="Invoice", ondelete='cascade', index=True)

    @api.model
    def _get_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG15")
