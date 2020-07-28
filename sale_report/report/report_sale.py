
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class SaleReportReport(models.AbstractModel):
    _name = "report.sale_report.report_sale_report"
    _description = 'Report Sale'
    
    def _sum_total(self, sale_ids, currency_id):
        currency_obj = self.env['res.currency'].browse(currency_id)
        amount_total = 0.0
        margin = 0.0
        amount_untaxed = 0.0
        amount_tax = 0.0
        for order_id in sale_ids:
            amount_total += order_id.amount_total
            margin += order_id.margin
            amount_untaxed += order_id.amount_untaxed
            amount_tax += order_id.amount_tax
        format_amount_total = formatLang(sale_ids.env, amount_total, currency_obj = currency_obj)
        format_margin = formatLang(sale_ids.env, margin, currency_obj = currency_obj)
        format_amount_untaxed = formatLang(sale_ids.env, amount_untaxed, currency_obj = currency_obj)
        format_amount_tax = formatLang(sale_ids.env, amount_tax, currency_obj = currency_obj)
        return {'amount_total':format_amount_total,'margin':format_margin,'amount_untaxed':format_amount_untaxed,'amount_tax':format_amount_tax}

    def _get_margin(self, line):
        if line.purchase_price:
            margin = line.margin*100/(line.purchase_price*line.product_uom_qty)
            return {'margin': margin, 'fmargin' : formatLang(line.env, margin, digits=2)}
        else:
            return {'margin': 100.0, 'fmargin' : formatLang(line.env, 100.0, digits=2)}
    
    @api.model
    def get_report_values(self, docids, data=None):
        sale_repor = self.env['sale.report.wizard'].browse(data['sale_repor_id'])
        sale_ids = self.env['sale.order'].browse((data['sale_ids']))
        docs = sale_ids
        if sale_repor.report_by == 'report_partner':
            docs = sale_ids.mapped('partner_id')
            data['name'] = _('Partner')
        elif sale_repor.report_by == 'report_user':
            docs = sale_ids.mapped('user_id')
            data['name'] = _('Salesperson')
        elif sale_repor.report_by == 'report_team':
            docs = sale_ids.mapped('team_id')
            data['name'] = _('Sales Channel')
        data['currency_ids'] = sale_ids.mapped('currency_id')
        data['sale_ids'] = sale_ids
        return {'docs': sale_repor, 'data':data, 'sale_report': self}
    