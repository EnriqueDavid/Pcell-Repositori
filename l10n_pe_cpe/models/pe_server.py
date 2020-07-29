# -*- coding: utf-8 -*-
from odoo import models, fields, api


class pe_sunat_server(models.Model):
    _inherit = 'pe.server'

    server_type = fields.Selection([('sunat', 'SUNAT'),
                                    ('telefonica', 'Telefonica')], "Servidor", default="sunat")
