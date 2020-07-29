
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class SaleReportReport(models.AbstractModel):
    _name = "report.account_payment_report.report_account_payment"
    
    def _sum_total(self, payment_ids, currency_id):
        amount = 0.0
        payment_difference = 0.0
        for payment_id in payment_ids:
            amount += payment_id.amount
            payment_difference += payment_id.payment_difference
        format_amount = formatLang(payment_ids.env, amount, currency_obj = currency_id)
        #format_amount_total = formatLang(payment_ids.env, amount+amount_opening, currency_obj = currency_id)
        format_payment_difference = formatLang(payment_ids.env, payment_difference, currency_obj = currency_id)
        return {'amount':format_amount,'payment_difference':format_payment_difference}
    
    @api.model
    def get_report_values(self, docids, data=None):
        payment_repor = self.env['account.payment.report.wizard'].browse(data['payment_repor_id'])
        payment_ids = self.env['account.payment'].browse((data['payment_ids']))
        if payment_repor.report_by == 'report_partner':
            data['partner_ids']  =  payment_ids.mapped('partner_id')
            data['name'] = _('Partner')
        elif payment_repor.report_by == 'report_user':
            data['user_ids'] = payment_ids.mapped('payment_user_id')
            data['name'] = _('User')
        data['currency_ids'] = payment_ids.mapped('currency_id')
        data['payment_ids'] = payment_ids
        docs = payment_ids.mapped('journal_id')
        return {'docs': docs, 'data':data, 'payment_report': self}