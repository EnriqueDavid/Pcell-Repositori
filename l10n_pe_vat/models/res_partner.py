# -*- encoding: utf-8 -*-
import requests
import logging

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

STATE = [('ACTIVO', 'ACTIVO'),
         ('BAJA DE OFICIO', 'BAJA DE OFICIO'),
         ('BAJA DEFINITIVA', 'BAJA DEFINITIVA'),
         ('BAJA PROVISIONAL', 'BAJA PROVISIONAL'),
         ('SUSPENSION TEMPORAL', 'BAJA PROVISIONAL'),
         ('INHABILITADO-VENT.UN', 'INHABILITADO-VENT.UN'),
         ('BAJA MULT.INSCR. Y O', 'BAJA MULT.INSCR. Y O'),
         ('PENDIENTE DE INI. DE', 'PENDIENTE DE INI. DE'),
         ('OTROS OBLIGADOS', 'OTROS OBLIGADOS'),
         ('NUM. INTERNO IDENTIF', 'NUM. INTERNO IDENTIF'),
         ('ANUL.PROVI.-ACTO ILI', 'ANUL.PROVI.-ACTO ILI'),
         ('ANULACION - ACTO ILI', 'ANULACION - ACTO ILI'),
         ('BAJA PROV. POR OFICI', 'BAJA PROV. POR OFICI'),
         ('ANULACION - ERROR SU', 'ANULACION - ERROR SU')]

CONDITION = [('HABIDO', 'HABIDO'),
             ('NO HABIDO', 'NO HABIDO'),
             ('NO HALLADO', 'NO HALLADO'),
             ('PENDIENTE', 'PENDIENTE'),
             ('NO HALLADO SE MUDO D', 'NO HALLADO SE MUDO D'),
             ('NO HALLADO NO EXISTE', 'NO HALLADO NO EXISTE'),
             ('NO HALLADO FALLECIO', 'NO HALLADO FALLECIO'),
             ('-', 'NO HABIDO'),
             ('NO HALLADO OTROS MOT', 'NO HALLADO OTROS MOT'),
             ('NO APLICABLE', 'NO APLICABLE'),
             ('NO HALLADO NRO.PUERT', 'NO HALLADO NRO.PUERT'),
             ('NO HALLADO CERRADO', 'NO HALLADO CERRADO'),
             ('POR VERIFICAR', 'POR VERIFICAR'),
             ('NO HALLADO DESTINATA', 'NO HALLADO DESTINATA'),
             ('NO HALLADO RECHAZADO', 'NO HALLADO RECHAZADO')]

API_DNI = 'https://api.sistemerp.com/dni/'
API_RUC = 'http://api.sistemerp.com/ruc/'


class Partner(models.Model):
    _inherit = 'res.partner'

    doc_type = fields.Char(
        related="l10n_latam_identification_type_id.l10n_pe_vat_code")
    doc_number = fields.Char("Document Number")
    commercial_name = fields.Char("Commercial Name", default="-",
                                  help='If you do not have a commercial name, put "-" without quotes')
    legal_name = fields.Char("Legal Name", default="-",
                             help='If you do not have a legal name, put "-" without quotes')
    state = fields.Selection(STATE, 'State Partner', default="ACTIVO")
    condition = fields.Selection(CONDITION, 'Condition', default='HABIDO')
    activities_ids = fields.Many2many("pe.datas", string="Economic Activities", domain=[
                                      ('table_code', '=', 'PE.CIIU')])
    main_activity = fields.Many2one("pe.datas", string="Main Economic Activity", domain=[
                                    ('table_code', '=', 'PE.CIIU')])
    retention_agent = fields.Boolean("Is Agent")
    retention_agent_from = fields.Date("From")
    retention_agent_resolution = fields.Char("Resolution")
    is_validate = fields.Boolean("Is Validated")
    type_taxpayer = fields.Char("Type Taxpayer")
    emission_system = fields.Char("Emission System")
    accounting_system = fields.Char("Accounting System")
    last_update = fields.Datetime("Last Update")
    representative_ids = fields.One2many(
        "res.partner.representative", "partner_id", "Representatives")

    @api.constrains("doc_number")
    def check_doc_number(self):
        if not self.parent_id:
            for partner in self:
                doc_type = partner.l10n_latam_identification_type_id.l10n_pe_vat_code
                if not doc_type and not partner.doc_number:
                    continue
                elif doc_type == "0":
                    continue
                elif doc_type and not partner.doc_number:
                    raise ValidationError(_("Enter the document number"))
                vat = partner.doc_number
                if doc_type == '6':
                    check = self.validate_ruc(vat)
                    if not check:
                        _logger.info(
                            "The RUC Number [%s] is not valid !" % vat)
                        raise ValidationError(
                            _('the RUC entered is incorrect'))
                if self.search_count([('company_id', '=', partner.company_id.id),
                                      ('l10n_latam_identification_type_id.l10n_pe_vat_code',
                                       '=', doc_type),
                                      ('doc_number', '=', partner.doc_number)]) > 1:
                    raise ValidationError(
                        _('Document Number already exists and violates unique field constrain'))

    @api.onchange('l10n_latam_identification_type_id')
    def onchange_company_type(self):
        doc_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
        if doc_type == "6":
            self.company_type = 'company'
        else:
            self.company_type = 'person'
        super(Partner, self).onchange_company_type()

    @staticmethod
    def validate_ruc(vat):
        factor = '5432765432'
        sum = 0
        dig_check = False
        if len(vat) != 11:
            return False
        try:
            int(vat)
        except ValueError:
            return False
        for f in range(0, 10):
            sum += int(factor[f]) * int(vat[f])
        subtraction = 11 - (sum % 11)
        if subtraction == 10:
            dig_check = 0
        elif subtraction == 11:
            dig_check = 1
        else:
            dig_check = subtraction
        if not int(vat[10]) == dig_check:
            return False
        return True

    @api.onchange("doc_number", "l10n_latam_identification_type_id")
    @api.depends("l10n_latam_identification_type_id", "doc_number")
    def _doc_number_change(self):
        vat = self.doc_number
        if vat and self.l10n_latam_identification_type_id:
            vat_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
            if vat_type == '1':
                if len(vat) != 8:
                    raise UserError(_('the DNI entered is incorrect'))
                try:
                    response = requests.get(
                        '{}{}/'.format(API_DNI, vat.strip()), timeout=300)
                except Exception:
                    reponse = False
                if response and response.status_code != 200:
                    vals = {'detail': "Not found."}
                else:
                    vals = response and response.json() or {
                        'detail': "Not found."}
                if vals:
                    self.name = "%s %s, %s" % (vals.get('paternal_surname', ''), vals.get(
                        'maternal_surname', ''), vals.get('name', ''))
                    self.company_type = "person"
                    self.is_validate = True
                self.vat = "%s" % (vat)
                self.company_type = "person"
                self.country_id = 173

            elif vat_type == "6":
                if not self.validate_ruc(vat):
                    raise UserError(_('the RUC entered is incorrect'))
                try:
                    if self.env.context.get('force_update'):
                        response = requests.get(
                            '{}{}/?force_update=1'.format(API_RUC, vat.strip()))
                    else:
                        response = requests.get(
                            '{}{}/'.format(API_RUC, vat.strip()))
                except Exception:
                    reponse = False

                vals = response and response.json() or {'detail': "Not found."}

                if vals:
                    self.commercial_name = vals.get('commercial_name')
                    self.legal_name = vals.get('legal_name')
                    self.name = vals.get('legal_name')
                    self.street = vals.get('street', False)
                    self.company_type = "company"
                    self.state = vals.get('state', False)
                    self.condition = vals.get('condition')
                    self.type_taxpayer = vals.get('type_taxpayer')
                    self.emission_system = vals.get('emission_system')
                    self.accounting_system = vals.get('accounting_system')
                    self.is_validate = True
                    if vals.get('activities'):
                        activities_ids = []
                        for activity in vals.get('activities'):
                            ciiu = self.env['pe.datas'].search(
                                [('code', '=', activity.get('code')), ('table_code', '=', 'PE.CIIU')], limit=1)
                            if ciiu:
                                activities_ids.append(ciiu.id)
                            else:
                                activity['table_code'] = 'PE.CIIU'
                                ciiu = self.env['pe.datas'].sudo().create(
                                    activity)
                                activities_ids.append(ciiu.id)
                        if activities_ids:
                            self.main_activity = activities_ids[-1]
                            if self.activities_ids:
                                self.activities_ids = [
                                    (6, None, activities_ids)]
                            else:
                                act = []
                                for activity_id in activities_ids:
                                    act.append((4, activity_id))
                                self.activities_ids = act
                    if vals.get('representatives'):
                        representatives = []
                        for rep in vals.get('representatives'):
                            representatives.append((0, None, rep))
                            # if rep.get('position', '') in ["GERENTE GENERAL", "TITULAR-GERENTE", "GERENTE"]:
                            #    contact={}
                            #    contact['name']= rep.get('name')
                            #    if self.search_count([('name', '=', contact['name']), ('parent_id', '=', self.id)])==0:
                            #        contact['function']=rep.get('position')
                            #        contact['type']='contact'
                            #        contact['parent_id']=self.id
                            #        #child_id=self.create(contact)
                            #        self.child_ids=[(0, None, contact)]
                        if self.representative_ids:
                            self.representative_ids.unlink()
                        self.representative_ids = representatives
                    self.retention_agent = vals.get('retention_agent', False)
                    self.retention_agent_from = vals.get(
                        'retention_agent_from', False)
                    self.retention_agent_resolution = vals.get(
                        'retention_agent_resolution', False)

                    if vals.get('district') and vals.get('province'):
                        district = self.env['l10n_pe.res.city.district'].search([('name', 'ilike', vals.get('district')),
                                                                                 ('city_id.name', 'ilike', vals.get('province'))])
                        if len(district) == 1:
                            self.l10n_pe_district = district.id
                            self.city_id = district.city_id.id
                            self.state_id = district.city_id.state_id.id
                        elif len(district) == 0:
                            province = self.env['res.city'].search(
                                [('name', 'ilike', vals.get('province'))])
                            if len(province) == 1:
                                self.city_id = province.id
                                self.state_id = district.city_id.state_id.id
                        else:
                            province = self.env['res.city'].search(
                                [('name', 'ilike', vals.get('province'))])
                            if len(province) == 1:
                                self.city_id = province.id
                                district = self.env['l10n_pe.res.city.district'].search([('name', '=ilike', vals.get('district')),
                                                                                         ('city_id.name', 'ilike', self.city_id.name)])
                                if len(district) == 1:
                                    self.l10n_pe_district = district.id

                self.vat = "%s" % vat
            elif (vat_type != '6') or (vat_type != '1'):
                self.vat = "%s" % (self.doc_number)

    @api.onchange('vat')
    def _vat_change(self):
        if self.vat:
            vat = len(self.vat) >= 1 and self.vat or ""
            doc_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code or False

            if vat:
                if doc_type == "0":
                    self.doc_type = "0"
                elif doc_type == "1":
                    if len(vat) != 8:
                        raise UserError(_('the DNI entered is incorrect'))
                    self.doc_type = "1"
                elif doc_type == "4":
                    self.doc_type = "4"
                elif doc_type == "6":
                    if not self.validate_ruc(vat):
                        raise UserError(_("the RUC entered is incorrect"))
                    self.doc_type = "6"
                elif doc_type == "A":
                    self.doc_type = "A"
                if self.doc_number != vat:
                    self.doc_number = vat
            else:
                self.doc_type = "7"
                if self.doc_number != vat:
                    self.doc_number = vat

    @api.onchange('country_id')
    def _onchange_country(self):
        pass

    @api.onchange('l10n_pe_district')
    def _onchange_district_id(self):
        if self.l10n_pe_district:
            if not self.city_id:
                self.city_id = self.l10n_pe_district.city_id.id

    @api.onchange('city_id')
    def _onchange_province_id(self):
        if self.city_id:
            return {'domain': {'l10n_pe_district': [('city_id', '=', self.city_id.id)]}}
        else:
            return {'domain': {'l10n_pe_district': []}}

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            return {'domain': {'city_id': [('state_id', '=', self.state_id.id)]}}
        else:
            return {'domain': {'city_id': []}}

    @api.model
    def change_commercial_name(self):
        partner_ids = self.search(
            [('commercial_name', '!=', '-'), ('doc_type', '=', '6')])
        for partner_id in partner_ids:
            partner_id.update_document()

    def update_document(self):
        self._doc_number_change()
        self._vat_change()

    @api.model
    def update_partner_datas(self):
        partner_ids = self.search([('doc_type', '=', '6')])
        for partner in partner_ids:
            partner.name = partner.commercial_name


class PartnerRepresentative(models.Model):
    _name = "res.partner.representative"
    _description = 'Representative Partner'

    name = fields.Char("Name")
    doc_type = fields.Char("Document Type")
    doc_number = fields.Char("Document Number")
    position = fields.Char("Position")
    date_from = fields.Date("Date From")
    partner_id = fields.Many2one("res.partner", "Partner")
