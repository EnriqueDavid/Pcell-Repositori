# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PeCertificate(models.Model):
    _name = 'pe.certificate'
    _description = 'Peruvian Certificate'

    name = fields.Char("Name", required=True)
    start_date = fields.Date("Start Date", required=True)
    end_date = fields.Date("End Date", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)
    key = fields.Text(".key", required=True)
    crt = fields.Text(".crt", required=True)
    pfx_name = fields.Char("pfx Name")
    pfx_datas = fields.Binary(".pfx")

    def action_draft(self):
        self.state = "draft"

    def action_done(self):
        self.state = "done"

    def action_cancel(self):
        self.state = "cancel"
