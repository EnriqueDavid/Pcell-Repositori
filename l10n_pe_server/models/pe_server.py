# -*- coding: utf-8 -*-
from odoo import models, fields, api


class pe_sunat_server(models.Model):
    _name = 'pe.server'
    _description = 'Peruvian Server'

    name = fields.Char("Name", required=True)
    url = fields.Char("Url", required=True)
    user = fields.Char("User")
    password = fields.Char("Password")
    description = fields.Text("Description")
    active = fields.Boolean("Active", default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)

    def action_draft(self):
        self.state = "draft"

    def action_done(self):
        self.state = "done"

    def action_cancel(self):
        self.state = "cancel"
