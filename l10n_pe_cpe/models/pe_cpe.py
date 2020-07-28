# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from .cpe import get_document, get_sign_document, send_sunat_cpe, get_ticket_status, get_response, get_document_invoice, get_status_cdr
from base64 import b64decode, b64encode
from lxml import etree
from datetime import datetime
from odoo.exceptions import Warning


class PeSunatCpe(models.Model):
    _name = 'pe.cpe'
    _description = 'Sunat Perú'

    name = fields.Char("Name", default="/")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generate', 'Generated'),
        ('send', 'Send'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)
    type = fields.Selection([
        ('sync', 'Synchronous'),
        ('rc', 'Daily Summary'),
        ('ra', 'Low communication'),
    ], string="Type", default='sync', states={'draft': [('readonly', False)]})
    date = fields.Date("Date", default=fields.Date.context_today, states={
                       'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('pe.sunat.cpe'))
    xml_document = fields.Text("XML Document", states={
                               'draft': [('readonly', False)]})
    datas = fields.Binary("XML Data", readonly=True)
    datas_fname = fields.Char("XML File Name",  readonly=True)
    datas_sign = fields.Binary("XML Sign Data",  readonly=True)
    datas_sign_fname = fields.Char("XML Sign File Name",  readonly=True)
    datas_zip = fields.Binary("XML Zip Data", readonly=True)
    datas_zip_fname = fields.Char("XML Zip File Name",  readonly=True)
    datas_response = fields.Binary("XML Response Data",  readonly=True)
    datas_response_fname = fields.Char(
        "XML Response File Name",  readonly=True)
    response = fields.Char("Response", readonly=True)
    response_code = fields.Char("Response Code", readonly=True)
    note = fields.Text("Note", readonly=True)
    error_code = fields.Selection(
        "_get_error_code", string="Error Code", readonly=True)
    digest = fields.Char("Digest", readonly=True)
    signature = fields.Text("Signature", readonly=True)
    invoice_ids = fields.One2many(
        "account.move", 'pe_cpe_id', string="Invoices", readonly=True)
    ticket = fields.Char("Ticket", readonly=True)
    date_end = fields.Datetime(
        "End Date", states={'draft': [('readonly', False)]})
    send_date = fields.Datetime(
        "Send Date", states={'draft': [('readonly', False)]})
    voided_ids = fields.One2many(
        "account.move", "pe_voided_id", string="Voided Invoices")
    summary_ids = fields.One2many(
        "account.move", "pe_summary_id", string="Summary Invoices")
    is_voided = fields.Boolean("Is Boided")

    _order = 'date desc, name desc'

    def unlink(self):
        for batch in self:
            if batch.name != "/" and batch.state != "draft":
                raise Warning(_('You can only delete sent documents.'))
        return super(PeSunatCpe, self).unlink()

    @api.model
    def _get_error_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

    def action_draft(self):
        if not self.xml_document and self.type == "sync":
            self._prepare_cpe()
        self.state = 'draft'

    def action_generate(self):
        if not self.xml_document and self.type == "sync":
            self._prepare_cpe()
        elif self.type == "sync" and self.name != "/":
            if self.get_document_name() != self.name:
                self._prepare_cpe()
        if self.type == "sync":
            self._sign_cpe()
        self.state = 'generate'

    def action_send(self):
        state = self.send_cpe()
        if state:
            self.state = state

    def action_verify(self):
        self.state = 'verify'

    def action_done(self):
        if self.type in ['rc', 'ra']:
            status = self.get_sunat_ticket_status()
            if status and self.type == 'rc':
                if self.is_voided == False:
                    for invoice_id in self.summary_ids.filtered(lambda inv: inv.state in ['annul']):
                        pe_summary_id = self.get_cpe_async(
                            "rc", invoice_id, True)
                        invoice_id.pe_summary_id = pe_summary_id.id
                        # if not pe_summary_id.is_voided:
                        #    pe_summary_id.is_voided = True
            if status:
                self.state = status
        else:
            self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    @api.model
    def create_from_invoice(self, invoice_id):
        vals = {}
        vals['invoice_ids'] = [(4, invoice_id.id)]
        vals['type'] = 'sync'
        vals['company_id'] = invoice_id.company_id.id
        res = self.create(vals)
        return res

    @api.model
    def get_cpe_async(self, type, invoice_id, is_voided=False):
        res = None
        company_id = invoice_id.company_id.id
        date_invoice = invoice_id.invoice_date
        cpe_ids = self.search([('state', '=', 'draft'), ('type', '=', type), ('date', '=', date_invoice),
                               ('name', '=', "/"), ('company_id', '=', company_id), ('is_voided', '=', is_voided)], order="date DESC")
        for cpe_id in cpe_ids:
            if cpe_id and len(cpe_id.summary_ids.ids) < 500:
                res = cpe_id
                break
        if not res:
            vals = {}
            vals['type'] = type
            vals['date'] = date_invoice
            vals['company_id'] = company_id
            vals['is_voided'] = is_voided
            res = self.create(vals)
        return res

    def get_document_name(self):
        self.ensure_one()
        ruc = self.company_id.partner_id.doc_number
        if self.type == "sync":
            doc_code = "-%s" % self.invoice_ids[0].journal_id.pe_invoice_code
            if self.name and self.name != '/':
                number = self.name
            else:
                number = self.invoice_ids[0].name
                self.name = number
        else:
            doc_code = ""
            number = self.name or ""
        return "%s%s-%s" % (ruc, doc_code, number)

    def prepare_sunat_auth(self):
        self.ensure_one()
        res = {}
        if self.company_id.pe_cpe_server_id.server_type == 'telefonica':
            res['ruc'] = ''
        else:
            res['ruc'] = self.company_id.partner_id.doc_number
        res['username'] = self.company_id.pe_cpe_server_id.user
        res['password'] = self.company_id.pe_cpe_server_id.password
        res['url'] = self.company_id.pe_cpe_server_id.url
        res["server"] = self.company_id.pe_cpe_server_id.server_type
        return res

    # @api.one
    def _prepare_cpe(self):
        if not self.xml_document:
            file_name = self.get_document_name()
            xml_document = get_document(self)
            self.xml_document = xml_document
            self.datas = b64encode(xml_document)
            self.datas_fname = file_name+".xml"

    # @api.one
    def _sign_cpe(self):
        file_name = self.get_document_name()
        if not self.xml_document:
            self._prepare_cpe()
        if self.xml_document.encode('utf-8') != b64decode(self.datas):
            self.datas = b64encode(self.xml_document.encode('utf-8'))
            #self.datas_fname = file_name+".xml"
        key = self.company_id.pe_certificate_id.key
        crt = self.company_id.pe_certificate_id.crt
        self.datas_sign = b64encode(
            get_sign_document(self.xml_document, key, crt))
        self.datas_sign_fname = file_name+".xml"
        self.get_sign_details()

    def send_cpe(self):
        res = None
        self.ensure_one()
        if not self.send_date:
            # record = self.with_context(tz = "America/Lima")
            record = self.with_context(tz=self.env.user.tz)
            self.send_date = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(record, datetime.now()))
        local_date = datetime.strptime(
            str(self.send_date), "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
        if self.type == "sync" and self.name == "/":
            self.name = self.invoice_ids[0].number
        elif self.type == "ra" and self.name == "/":
            self.name = self.env['ir.sequence'].with_context(
                ir_sequence_date=local_date).next_by_code('pe.sunat.cpe.ra')
        elif self.type == "rc" and self.name == "/":
            self.name = self.env['ir.sequence'].with_context(
                ir_sequence_date=local_date).next_by_code('pe.sunat.cpe.rc')
        file_name = self.get_document_name()
        if self.type in ["rc", "ra"]:
            self._prepare_cpe()
            self._sign_cpe()
            self.datas_fname = file_name+".xml"
            self.datas_sign_fname = file_name+".xml"
        client = self.prepare_sunat_auth()
        document = {}
        document['document_name'] = file_name
        document['type'] = self.type
        document['xml'] = b64decode(self.datas_sign)
        self.datas_zip, response_status, response, response_data = send_sunat_cpe(
            client, document)
        self.datas_zip_fname = file_name+".zip"
        if response_status:
            res = "verify"
            if self.type == "sync":
                self.datas_response = response_data
                new_state = self.get_response_details()
                self.datas_response_fname = 'R-%s.zip' % file_name
                res = new_state or res
            else:
                self.ticket = response_data
        else:
            res = "send"
            self.response = response.get("faultcode")
            self.note = response.get("faultstring")
            if response.get("faultcode"):
                code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
                    response.get("faultcode").split(".")[-1].encode('utf-8')) or False
                self.response_code = code
                self.error_code = code
        return res

    # @api.multi
    def get_sign_details(self):
        self.ensure_one()
        vals = {}
        tag = etree.QName('http://www.w3.org/2000/09/xmldsig#', 'DigestValue')
        xml_sign = b64decode(self.datas_sign)
        digest = etree.fromstring(xml_sign).find('.//'+tag.text)
        if digest != -1:
            self.digest = digest.text
        tag = etree.QName(
            'http://www.w3.org/2000/09/xmldsig#', 'SignatureValue')
        sign = etree.fromstring(xml_sign).find('.//'+tag.text)
        if sign != -1:
            self.signature = sign.text

    # @api.multi
    @api.depends('datas_response')
    def get_response_details(self):
        self.ensure_one()
        vals = {}
        state = self.state
        if self.datas_response:
            try:
                file_name = self.get_document_name()
                xml_response = get_response(
                    {'file': self.datas_response, 'name': 'R-%s.xml' % file_name})
                sunat_response = etree.fromstring(xml_response)
                cbc = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
                tag = etree.QName(cbc, 'ResponseDate')
                date = sunat_response.find('.//'+tag.text)
                tag = etree.QName(cbc, 'ResponseTime')
                time = sunat_response.find('.//'+tag.text)
                if time != -1 and date != -1:
                    # self.date_end = fields.Datetime.context_timestamp(self, datetime.now())
                    # record = self.with_context(tz = "America/Lima")
                    record = self.with_context(tz=self.env.user.tz)
                    self.date_end = fields.Datetime.to_string(
                        fields.Datetime.context_timestamp(record, datetime.now()))
                tag = etree.QName(cbc, 'ResponseCode')
                code = sunat_response.find('.//'+tag.text)
                res_code = ""
                if code != -1:
                    res_code = "%04d" % int(code.text)
                    self.response_code = res_code
                    if res_code == "0000":
                        self.error_code = False
                        state = "done"
                tag = etree.QName(cbc, 'Description')
                description = sunat_response.find('.//'+tag.text)
                res_desc = ""
                if description != -1:
                    res_desc = description.text
                self.response = "%s - %s" % (res_code, res_desc)
                notes = sunat_response.xpath(".//cbc:Note", namespaces={
                                             'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
                res_note = ""
                for note in notes:
                    res_note += note.text
                self.note = res_note
            except Exception as e:
                print('******* ERROR ********')
                print(e)
                print('******* ERROR ********')
                pass
        return state

    # @api.one
    def generate_cpe(self):
        self._prepare_cpe()
        self._sign_cpe()
        self.state = "generate"

    # @api.multi
    def get_sunat_ticket_status(self):
        self.ensure_one()
        client = self.prepare_sunat_auth()
        response_status, response, response_file = get_ticket_status(
            self.ticket, client)
        state = None
        if response_status:
            file_name = self.get_document_name()
            self.datas_response = response_file
            self.datas_response_fname = 'R-%s.zip' % file_name
            state = self.get_response_details()
        else:
            res = "send"
            self.response = response.get("faultcode", False)
            self.note = response.get("faultstring", False)
            if response.get("faultcode", False):
                code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
                    response.get("faultcode").split(".")[-1].encode('utf-8')) or False
                self.error_code = code
        if self.type == "rc":
            for invoice_id in self.summary_ids:
                if invoice_id.pe_cpe_id.name == "/":
                    invoice_id.pe_cpe_id.name = invoice_id.move_name
                invoice_id.pe_cpe_id.response = self.response
                if state and response_status:
                    invoice_id.pe_cpe_id.state = state
        return state

    # @api.one
    def action_document_status(self):
        client = self.prepare_sunat_auth()
        name = self.get_document_name()
        response_status, response, response_file = get_status_cdr(name, client)
        state = None
        if response_status:
            self.note = "%s - %s" % (response['statusCdr'].get(
                'statusCode', ""), response['statusCdr'].get('statusMessage', ""))
            if response_file:
                self.datas_response = response_file
                self.datas_response_fname = 'R-%s.zip' % name
                state = self.get_response_details()
                if state:
                    self.state = state
        else:
            self.response = response.get("faultcode", False)
            self.note = response.get("faultstring") or str(response)
            if response.get("faultcode"):
                try:
                    code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
                        response.get("faultcode").split(".")[-1].encode('utf-8')) or False
                    self.error_code = code
                except:
                    pass

    # @api.multi
    def send_rc(self):
        cpe_ids = self.search(
            [('state', 'in', ['draft', 'generate', 'verify']), ('type', 'in', ['rc'])])
        for cpe_id in cpe_ids:
            try:
                if cpe_id.ticket:
                    cpe_id.action_done()
                else:
                    cpe_id.action_generate()
                    cpe_id.action_send()
            except Exception:
                pass

    # @api.multi
    def send_ra(self):
        cpe_ids = self.search(
            [('state', 'in', ['draft', 'generate', 'verify']), ('type', 'in', ['ra'])])
        for cpe_id in cpe_ids:
            try:
                if cpe_id.ticket:
                    cpe_id.action_done()
                else:
                    check = True
                    for invoice_id in cpe_id.invoice_ids:
                        if invoice_id.pe_invoice_code in ["03"] and invoice_id.origin_doc_code in ["03"]:
                            if invoice_id.pe_summary_id.state not in ['verify', 'done']:
                                check = False
                                break
                    if check:
                        cpe_id.action_generate()
                        cpe_id.action_send()
            except Exception:
                pass

    # @api.multi
    def send_async_cpe(self):
        cpe_ids = self.search(
            [('state', 'in', ['generate', 'send']), ('type', 'in', ['sync'])])
        for cpe_id in cpe_ids:
            if cpe_id.invoice_ids:
                if cpe_id.invoice_ids[0].pe_invoice_code not in ["03", "07"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03", "07"]:
                    try:
                        cpe_id.action_document_status()
                    except Exception:
                        pass
                if cpe_id.state != 'done':
                    if cpe_id.invoice_ids[0].pe_invoice_code not in ["03", "07"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03", "07"]:
                        try:
                            cpe_id.action_generate()
                            cpe_id.action_send()
                        except Exception:
                            pass

    def send_async_cpe_nc(self):
        cpe_ids = self.search(
            [('state', 'in', ['generate', 'send']), ('type', 'in', ['sync'])])
        for cpe_id in cpe_ids:
            if cpe_id.invoice_ids:
                if cpe_id.invoice_ids[0].pe_invoice_code not in ["03", "01"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03"]:
                    try:
                        cpe_id.action_document_status()
                    except Exception:
                        pass
                if cpe_id.state != 'done':
                    if cpe_id.invoice_ids[0].pe_invoice_code not in ["03", "01"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03"]:
                        try:
                            cpe_id.action_generate()
                            cpe_id.action_send()
                        except Exception:
                            pass
