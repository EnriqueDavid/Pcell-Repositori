# -*- coding: utf-8 -*-

import odoo
import sys
import datetime
from itertools import groupby
from imp import reload
from odoo import fields, models, api, tools, _
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero
from . import amount_to_text
import logging


try:
    from num2words import num2words
except ImportError:
    logging.getLogger(__name__).warning(
        "The num2words python library is not installed, l10n_mx_edi features won't be fully available.")
    num2words = None


class PurchaseOrder(models.Model):

    """ To create invoice for purchase order line"""

    _inherit = 'purchase.order'

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        if invoice_vals:
            invoice_vals.update(
                {'report_template_id': self.partner_id and self.partner_id.report_template_id.id or False})
        return invoice_vals


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if invoice_vals:
            invoice_vals.update(
                {'report_template_id': self.partner_invoice_id and self.partner_invoice_id.report_template_id.id or False})
        return invoice_vals


class AccountMove(models.Model):
    _inherit = 'account.move'

    def order_lines_layouted(self):
        res = super(AccountMove, self).order_lines_layouted()
        self.ensure_one()
        report_pages = [[]]
        result = self.env['res.config.settings'].get_values()
        if result['group_sale_layout'] != False:
            for category, lines in groupby(self.invoice_line_ids, lambda l: l.layout_category_id):

                if category:
                    if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
                        report_pages.append([])

                    report_pages[-1].append({
                        'name': category and category.name,
                        'subtotal': category and category.subtotal,
                        'pagebreak': category and category.pagebreak,
                        'lines': list(lines)
                    })
                else:
                    report_pages.append([])
                    report_pages[-1].append({
                        'name': _('Uncategorized'),
                        'subtotal': category.subtotal,
                        'pagebreak': True,
                        'lines': list(lines)
                    })
        else:
            for category, lines in groupby(self.invoice_line_ids, lambda l: l.layout_category_id):

                report_pages[-1].append({
                    'name': category and category.name,
                    'subtotal': category and category.subtotal,
                    'pagebreak': category and category.pagebreak,
                    'lines': list(lines)
                })
        return report_pages

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        result = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id:
            self.report_template_id = self.partner_id.report_template_id.id or False
        return result

    @api.model
    def _default_report_template(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), (
            'report_name', '=', 'sistemerp_ereport_template.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search(
                [('model', '=', 'account.move')])[0]
        return report_id

    @api.depends('partner_id')
    def _default_report_template1(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), (
            'report_name', '=', 'sistemerp_ereport_template.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search(
                [('model', '=', 'account.move')])[0]
        if self.report_template_id and self.report_template_id.id < report_id.id:
            self.write(
                {'report_template_id': report_id and report_id.id or False})
            #self.report_template_id = report_id and report_id.id or False
        self.report_template_id = self.report_template_id or False
        self.report_template_id1 = report_id and report_id.id or False

    # @api.multi
    # def invoice_print(self):
    #     """ Print the invoice and mark it as sent, so that we can see more
    #         easily the next step of the workflow
    #     """
    #     self.ensure_one()
    #     self.sent = True
    #     res = super(AccountMove, self).invoice_print()
    #     if self.report_template_id or self.partner_id and self.partner_id.report_template_id or self.company_id and self.company_id.report_template_id:
    #         report_id = self.report_template_id or self.partner_id and self.partner_id.report_template_id or self.company_id and self.company_id.report_template_id
    #         if report_id:
    #             report = report_id.report_action(self)
    #             return report
    #     return res

    def _get_street(self, partner):
        self.ensure_one()
        address = ''
        if partner.street:
            address = "%s" % (partner.street)
        if partner.street2:
            address += ", %s" % (partner.street2)
        reload(sys)
        # sys.setdefaultencoding("utf-8")
        html_text = str(tools.plaintext2html(address, container_tag=True))
        data = html_text.split('p>')
        if data:
            return data[1][:-2]
        return False

    def _get_address_details(self, partner):
        self.ensure_one()
        address = ''
        if partner.city:
            address = "%s" % (partner.city)
        if partner.state_id.name:
            address += ", %s" % (partner.state_id.name)
        if partner.zip:
            address += ", %s" % (partner.zip)
        if partner.country_id.name:
            address += ", %s" % (partner.country_id.name)
        reload(sys)
        # sys.setdefaultencoding("utf-8")
        html_text = str(tools.plaintext2html(address, container_tag=True))
        data = html_text.split('p>')
        if data:
            return data[1][:-2]
        return False

    def _get_origin_date(self, origin):
        self.ensure_one()
        if self.type in ('in_invoice', 'in_refund'):
            sale_obj = self.env['purchase.order']
        else:
            sale_obj = self.env['sale.order']
        lang = self._context.get("lang")
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'en_US')])
        sale = sale_obj.search([('name', '=', origin)])
        if sale:
            timestamp = datetime.datetime.strptime(
                str(sale.date_order), tools.DEFAULT_SERVER_DATETIME_FORMAT)
            ts = odoo.fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format)  # .decode('utf-8')
            if sale:
                return n_date
        return False

    def _get_origin_reference(self, origin):
        self.ensure_one()
        if self.type in ('in_invoice', 'in_refund'):
            sale_obj = self.env['purchase.order']
        else:
            sale_obj = self.env['sale.order']
        sale = sale_obj.search([('name', '=', origin)])
        if sale:
            order_ref = sale.client_order_ref
            if sale:
                return order_ref
        return False

    def _get_invoice_date(self):
        self.ensure_one()
        lang = self._context.get("lang")
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'es_PE')])
        if self.invoice_date:
            timestamp = datetime.datetime.strptime(
                str(self.invoice_date), tools.DEFAULT_SERVER_DATE_FORMAT)
            ts = odoo.fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format)  # .decode('utf-8')
            if self:
                return n_date
        return False

    def _get_invoice_due_date(self):
        self.ensure_one()
        lang = self._context.get("lang")
        lang_obj = self.env['res.lang']
        ids = lang_obj.search([("code", "=", lang or 'es_PE')])
        if self.invoice_date_due:
            timestamp = datetime.datetime.strptime(
                str(self.invoice_date_due), tools.DEFAULT_SERVER_DATE_FORMAT)
            ts = odoo.fields.Datetime.context_timestamp(self, timestamp)
            n_date = ts.strftime(ids.date_format)  # .decode('utf-8')
            if self:
                return n_date
        return False

    def _get_tax_amount(self, amount, payment=None):
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        res = formatLang(self.env, amount, currency_obj=currency)
        # for payment in self.payment_move_line_ids:
        if payment != None:
            if self.type in ('out_invoice', 'in_refund'):
                amount = sum(
                    [p.amount for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                amount_currency = sum(
                    [p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
            elif self.type in ('in_invoice', 'out_refund'):
                amount = sum(
                    [p.amount for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                amount_currency = sum(
                    [p.amount_currency for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
            # get the payment value in invoice currency
            if payment.currency_id and payment.currency_id == self.currency_id:
                amount_to_show = amount_currency
            else:
                amount_to_show = payment.company_id.currency_id.with_context(
                    date=payment.date).compute(amount, self.currency_id)
            if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                return res
            res = formatLang(self.env, amount_to_show, currency_obj=currency)
        return res

    report_template_id1 = fields.Many2one('ir.actions.report', string="Invoice Template1", compute='_default_report_template1',
                                          help="Please select Template report for Invoice", domain=[('model', '=', 'account.move')])
    report_template_id = fields.Many2one('ir.actions.report', string="Invoice Template",
                                         help="Please select Template report for Invoice", domain=[('model', '=', 'account.move')])
    amount_to_text = fields.Char(compute='_amount_in_words',
                                 string='In Words', help="The amount in words")

    @api.depends('amount_total', 'partner_id', 'partner_id.lang')
    def _amount_in_words(self):
        if self.partner_id.lang == 'nl_NL':
            self.amount_to_text = amount_to_text.amount_to_text_nl(
                self.amount_total, currency='euro')
        else:
            try:
                if self.partner_id.lang:
                    self.amount_to_text = num2words(
                        self.amount_total, lang=self.partner_id.lang).title()
                else:
                    self.amount_to_text = num2words(
                        self.amount_total, lang='en').title()
            except NotImplementedError:
                self.amount_to_text = num2words(
                    self.amount_total, lang='en').title()
