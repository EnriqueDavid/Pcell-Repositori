# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import formatLang


class AccountPaymentReportWizard(models.TransientModel):
    _name = "account.payment.report.wizard"
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    start_date = fields.Date("Start Date", default = fields.Date.context_today)
    end_date = fields.Date("End Date", default = fields.Date.context_today)
    report_by = fields.Selection([('report_user', 'By User'),
                                  ('report_partner','By Partner')], 'Report By', default = 'report_user')
    journal_ids = fields.Many2many('account.journal', string = 'Journal')
    partner_ids = fields.Many2many('res.partner', string = 'Partner')
    user_ids = fields.Many2many('res.users', string = 'Users')
    team_ids = fields.Many2many('crm.team', string = 'Sales Channel')
    show_invoices = fields.Boolean("Show Invoices", default = True)
    state = fields.Selection([('draft', 'Draft'), 
                              ('posted', 'Posted'), 
                              ('sent', 'Sent'), 
                              ('reconciled', 'Reconciled'), 
                              ('cancelled', 'Cancelled')], string="Status")
    amount_opening = fields.Float("Opening Amount", digits=(16,2))
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], "Partner Type", default = "customer")
    
    
    
    def _prepare_sale_report(self):
        self.ensure_one()
        querry = []
        vals = {}
        if self.company_id:
            querry.append(('company_id','=', self.company_id.id))
        if self.start_date:
            querry.append(('payment_date','>=', self.start_date))
        if self.end_date:
            querry.append(('payment_date','<=', self.end_date))
        if self.journal_ids:
            querry.append(('journal_id','in', self.journal_ids.ids))
        if self.partner_ids and self.report_by == 'report_partner':
            querry.append(('partner_id','in', self.partner_ids.ids))
        elif self.user_ids and self.report_by == 'report_user':
            querry.append(('payment_user_id','in', self.user_ids.ids))
        elif self.team_ids and self.report_by == 'report_team':
            querry.append(('team_id','in', self.team_ids.ids))
        if self.state:
            querry.append(('state','=', self.state))
        if self.partner_type:
            querry.append(('partner_type','=',self.partner_type))
        payment_ids = self.env['account.payment'].search(querry)
        vals['start_date'] = self.start_date
        vals['end_date'] = self.end_date
        vals['report_by'] = self.report_by
        vals['payment_ids'] = payment_ids.ids
        vals['payment_repor_id'] = self.id
        vals['show_invoices'] = self.show_invoices
        vals['amount_opening'] = self.amount_opening
        vals['partner_type'] = self.partner_type
        return vals
    
    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        data =  self._prepare_sale_report()
        return self.env.ref('account_payment_report.action_report_account_payment').with_context(landscape=True).report_action(self, data=data)
    
    