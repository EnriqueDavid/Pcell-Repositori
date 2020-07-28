# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_cpe = fields.Boolean("Is CPE")
    is_synchronous = fields.Boolean("Is synchronous")
    is_homologation = fields.Boolean("Is homologation")


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_pe_edi_tax_code = fields.Selection(
        selection_add=[('7152', 'ICBPER - Consumption tax on plastic bags')])
    pe_tax_type = fields.Many2one(
        comodel_name="pe.datas", string="Tax Type",
        compute="_compute_pe_tax_type")
    pe_tax_code = fields.Selection("_get_pe_tax_code", string="Tax Code")
    pe_tier_range = fields.Selection(selection="_get_pe_tier_range", string="Type of System",
                                     help="Type of system to the ISC")
    pe_is_charge = fields.Boolean("Charge")

    @api.depends('l10n_pe_edi_tax_code')
    def _compute_pe_tax_type(self):
        for rec in self:
            domain = [
                ('code', '=', rec.l10n_pe_edi_tax_code),
                ('table_code', '=', 'PE.CPE.CATALOG5')]
            rec.pe_tax_type = rec.env['pe.datas'].search(
                domain, limit=1).id

    @api.model
    def _get_pe_tier_range(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG8")

    @api.model
    def _get_pe_tax_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG5")

    @api.onchange('pe_tax_type')
    def onchange_pe_tax_type(self):
        if self.pe_tax_type:
            self.pe_tax_code = self.pe_tax_type.code
