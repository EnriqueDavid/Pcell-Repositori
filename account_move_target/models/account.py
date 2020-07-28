# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountAccount(models.Model):
    _inherit = "account.account"
    
    is_target = fields.Boolean("Is target account")
    target_ids = fields.One2many("account.account.target", "account_id", "Target Account")

class AccountAccountTarget(models.Model):
    _name = "account.account.target"
    
    name = fields.Char("Name")
    debit_account_id = fields.Many2one("account.account", "Debit Account", required=True)
    credit_account_id = fields.Many2one("account.account", "Credit Account", required=True)
    target_journal_id = fields.Many2one("account.journal", "Journal", required=True)
    account_id = fields.Many2one('account.account', "Account")