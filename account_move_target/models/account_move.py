# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.one
    def _create_target_move(self):
        lines = {}
        for line_id in self.line_ids:
            if line_id.account_id.is_target:
                for target_id in line_id.account_id.target_ids:
                    line = []
                    if lines.get(target_id.target_journal_id.id):
                        line = lines[target_id.target_journal_id.id]
                    amount = line_id.debit or line_id.credit
                    debit_vals = {
                        'name': line_id.name,
                        'partner_id':line_id.partner_id.id or False,
                        'amount_currency':line_id.amount_currency,
                        'currency_id':line_id.currency_id.id or False,
                        'date_maturity':line_id.date_maturity,
                        'debit': amount,
                        'credit': 0.0,
                        'account_id': target_id.debit_account_id.id,
                        'tax_line_id': line_id.tax_line_id.id or False,
                    }
                    credit_vals = {
                        'name': line_id.name,
                        'partner_id':line_id.partner_id.id or False,
                        'amount_currency':line_id.amount_currency,
                        'currency_id':line_id.currency_id.id or False,
                        'date_maturity':line_id.date_maturity,
                        'debit': 0.0,
                        'credit': amount,
                        'account_id': target_id.credit_account_id.id,
                        'tax_line_id': line_id.tax_line_id.id or False,
                    }
                    line.append((0, 0, debit_vals))
                    line.append((0, 0, credit_vals))
                    lines[target_id.target_journal_id.id] = line
        if lines:
            journal_ids = self.line_ids.mapped('account_id').mapped('target_ids').mapped('target_journal_id').ids
            for journal_id in journal_ids:
                vals = {
                    'journal_id': journal_id,
                    'date': self.date,
                    'state': 'draft',
                    'ref': self.ref or self.name,
                    'line_ids': lines.get(journal_id, [])
                }
                move = self.env['account.move'].create(vals)
                move.post()

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()
        for move_id in self:
            move_id._create_target_move()
        return res
