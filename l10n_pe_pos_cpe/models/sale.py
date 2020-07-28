# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def prepare_pos_order(self):
        res = super(SaleOrder, self).prepare_pos_order()
        self.ensure_one()
        #journal_id = False
        # if self.partner_id.doc_type in ["6"]:
        #    journal_id=self.env['account.journal'].search([('company_id','=',self.company_id.id),
        #                                                   ('pe_invoice_code', '=', '01'),
        #                                                   ('type', '=', type)], limit=1)
        #    if journal_id:
        #        journal_id=journal_id.id
        # else:
        #    journal_id=self.env['account.journal'].search([('company_id','=',self.company_id.id),
        #                                                   ('pe_invoice_code', '=', '03'),
        #                                                   ('type', '=', type)], limit=1)
        #    if journal_id:
        #        journal_id=journal_id.id
        res['invoice_journal'] = self.env.context.get(
            'invoice_journal_id', False)
        return res
