# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleReportWizard(models.TransientModel):
    _name = "sale.report.wizard"
    _description = 'Sale Report Wizard'
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    start_date = fields.Date("Start Date", default = fields.Date.context_today)
    end_date = fields.Date("End Date", default = fields.Date.context_today)
    report_by = fields.Selection([('report_user', 'By Salesperson'),
                                  ('report_partner','By Partner'),
                                  ('report_team','By Sales Channel')], 'Report By', default = 'report_user')
    partner_ids = fields.Many2many('res.partner', string = 'Partner')
    user_ids = fields.Many2many('res.users', string = 'Salesperson')
    team_ids = fields.Many2many('crm.team', string = 'Sales Channel')
    show_lines = fields.Boolean("Show Lines", default = True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status')
    
    
    def _prepare_sale_report(self):
        self.ensure_one()
        querry = []
        vals = {}
        if self.company_id:
            querry.append(('company_id','=', self.company_id.id))
        if self.start_date:
            querry.append(('date_order','>=', self.start_date))
        if self.end_date:
            querry.append(('date_order','<=', self.end_date))
        if self.partner_ids and self.report_by == 'report_partner':
            querry.append(('partner_id','in', self.partner_ids.ids))
        elif self.user_ids and self.report_by == 'report_user':
            querry.append(('user_id','in', self.user_ids.ids))
        elif self.team_ids and self.report_by == 'report_team':
            querry.append(('team_id','in', self.team_ids.ids))
        if self.state:
            querry.append(('state','=', self.state))
        sale_ids = self.env['sale.order'].search(querry)
        if not sale_ids:
            raise ValidationError(_("There are no sales orders"))
        vals['start_date'] = self.start_date
        vals['end_date'] = self.end_date
        vals['report_by'] = self.report_by
        vals['sale_ids'] = sale_ids.ids
        vals['sale_repor_id'] = self.id
        vals['show_lines'] = self.show_lines
        return vals
    
    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        data =  self._prepare_sale_report()
        return self.env.ref('sale_report.action_report_sale_report').with_context(landscape=True).report_action(self, data=data)
    
    