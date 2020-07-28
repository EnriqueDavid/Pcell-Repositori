# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
import json
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Credit Note
    'in_refund': 'in_invoice',          # Vendor Credit Note
}


class PeRelatedInvoice(models.TransientModel):
    _name = "pe.related.invoice.wizard"
    _description = 'Related Invoice wizard'

    @api.model
    def default_get(self, fields_list):
        res = super(PeRelatedInvoice, self).default_get(fields_list)
        invoice_id = self.env['account.move'].browse(
            self.env.context.get('active_id', []))
        if invoice_id:
            res['name'] = invoice_id.name
            res['invoice_id'] = invoice_id.id
            res['date_invoice'] = invoice_id.date_invoice or fields.Date.context_today(
                invoice_id)
            res['partner_id'] = invoice_id.partner_id.id
            res['currency_id'] = invoice_id.currency_id.id
            res['journal_id'] = invoice_id.journal_id.id
            res['type'] = invoice_id.journal_id.type
            res['invoice_type_refund'] = TYPE2REFUND[invoice_id.type]
            res['company_id'] = invoice_id.company_id.id
            res['is_retention'] = invoice_id.journal_id.pe_invoice_code == '20'
            if invoice_id.type in ['out_invoice', 'in_invoice']:
                res['invoice_type'] = invoice_id.type
            else:
                res['invoice_type'] = TYPE2REFUND[invoice_id.type]
            lines = []
            # for line in invoice_id.invoice_line_ids.filtered(lambda s: s.pe_invoice_ids):
            #    vals= {}
            #    vals['name'] = line.name
            #    vals['account_id'] = line.account_id.id
            #    vals['quantity'] = line.quantity
            #    vals['uom_id'] = line.uom_id.id
            #    vals['amount_unit'] = line.price_unit
            #    vals['related_line_tax_ids'] = [(6,False,line.tax_ids.ids)]
            #    vals['invoice_ids'] = [(6,False,line.pe_invoice_ids.ids)]
            #    lines.append((0,False,vals))
            #res['related_ids'] = vals
        return res

    name = fields.Char("Name", required=True)
    invoice_id = fields.Many2one("account.move", "Invoice")
    date_invoice = fields.Date(
        string='Invoice Date', help="Keep empty to use the current date", required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    currency_id = fields.Many2one('res.currency', string='Currency')
    journal_id = fields.Many2one('account.journal', string='Journal')
    type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ], related='journal_id.type', string="Type")
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ], readonly=True, index=True, change_default=True,
        track_visibility='always')
    invoice_type_refund = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ], readonly=True, index=True, change_default=True,
        track_visibility='always')
    company_id = fields.Many2one('res.company', string='Company')
    related_ids = fields.One2many(comodel_name="pe.related.invoice.wizard.line",
                                  inverse_name="related_id", string="Related Invoices")
    is_retention = fields.Boolean("Retention")
    estimated_amount = fields.Float("Estimated Amount", digits=(16, 2))
    amount_total = fields.Float("Total", digits=(
        16, 2), compute="_compute_amount_total")

    # @api.multi
    @api.depends('related_ids.invoice_id')
    def _compute_amount_total(self):
        for line_id in self:
            amount_total = sum(
                line.inv_amount_total for line in line_id.related_ids)
            line_id.amount_total = amount_total

    # @api.multi
    def check_retention(self):
        self.ensure_one()
        if not self.is_retention or not self.invoice_id.get_pe_data_by_code('PE.CPE.CATALOG23', '01'):
            return True
        else:
            return False

    # @api.multi
    def proration_invoices(self):
        self.ensure_one()

        def _compute_amount(base_amount, quantity, tax_ids):
            for tax_id in tax_ids:
                if tax_id.amount_type == 'fixed':
                    if base_amount:
                        base_amount = math.copysign(
                            quantity, base_amount) / tax_id.amount
                    else:
                        base_amount = quantity / tax_id.amount
                elif (tax_id.amount_type == 'percent' and not tax_id.price_include):
                    base_amount = base_amount - \
                        (base_amount / (1 + tax_id.amount / 100))
                elif (tax_id.amount_type == 'percent' and tax_id.price_include) or (tax_id.amount_type == 'division' and tax_id.price_include):
                    base_amount = base_amount
                elif tax_id.amount_type == 'division' and not tax_id.price_include:
                    base_amount = base_amount / \
                        (1 - tax_id.amount / 100) - base_amount
            return base_amount
        lines = []
        amount_total = self.amount_total
        estimated_amount = self.estimated_amount or self.amount_total
        if self.related_ids:
            for line in self.related_ids:
                ratio = estimated_amount/amount_total
                invoice_amount = ratio * line.inv_amount_total
                for inv_line in line.invoice_id.invoice_line_ids:
                    line_ratio = invoice_amount/line.amount_total
                    amount = _compute_amount(
                        inv_line.price_total*line_ratio, inv_line.quantity, inv_line.tax_ids)
                    vals = {}
                    vals['product_id'] = inv_line.product_id.id
                    vals['name'] = "[%s] %s" % (
                        inv_line.invoice_id.move_name, inv_line.name)
                    vals['account_id'] = inv_line.account_id.id
                    vals['quantity'] = inv_line.quantity
                    vals['uom_id'] = inv_line.uom_id.id
                    vals['price_unit'] = amount/inv_line.quantity
                    vals['tax_ids'] = [(6, False, inv_line.tax_ids.ids)]
                    # [(6,False,line.invoice_ids.ids)]
                    vals['pe_invoice_id'] = inv_line.invoice_id.id
                    lines.append((0, False, vals))
        return lines
    # @api.one

    def create_related_invoices(self):
        invoice_id = self.invoice_id
        invoice_id.name = self.name
        invoice_id.date_invoice = self.date_invoice
        invoice_id.invoice_line_ids.unlink()
        lines = []
        if not self.check_retention():
            for line in self.related_ids:
                vals = {}
                vals['name'] = line.name
                vals['account_id'] = line.account_id.id
                vals['quantity'] = line.quantity
                vals['uom_id'] = line.uom_id.id
                vals['price_unit'] = line.amount_unit
                vals['tax_ids'] = [(6, False, line.related_line_tax_ids.ids)]
                # [(6,False,line.invoice_ids.ids)]
                vals['pe_invoice_id'] = line.invoice_id
                lines.append((0, False, vals))
        else:
            lines = self.proration_invoices()
        invoice_id.invoice_line_ids = lines

    @api.onchange("related_ids.invoice_id")
    def _onchange_invoice_ids(self):
        for line in self.related_ids:
            line._onchange_invoice_ids()
        return {}


class PeRelatedInvoiceLine(models.TransientModel):
    _name = "pe.related.invoice.wizard.line"
    _description = 'Related Move wizard line'

    @api.model
    def _default_account(self):
        if self._context.get('journal_id'):
            journal = self.env['account.journal'].browse(
                self._context.get('journal_id'))
            if self._context.get('type') in ('out_invoice', 'in_refund'):
                return journal.default_credit_account_id.id
            return journal.default_debit_account_id.id

    product_id = fields.Many2one("Product")
    name = fields.Char("Name", required=True)
    related_id = fields.Many2one('pe.related.invoice.wizard', 'Related')
    #multi_invoice = fields.Boolean("Multi invoice?")
    invoice_id = fields.Many2one('account.move', 'Invoice')
    #invoice_ids = fields.Many2many('account.move', string="Invoices", required=True)
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure',
                            required=True, default=1)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure',  index=True)
    amount_unit = fields.Monetary("Amount", required=True)
    related_line_tax_ids = fields.Many2many('account.tax',
                                            'pe_related_line_tax', 'invoice_line_id', 'tax_id',
                                            string='Taxes', domain=[('type_tax_use', '!=', 'none'), '|', ('active', '=', False), ('active', '=', True)])
    amount_subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_amount', help="Total amount without taxes")
    amount_total = fields.Monetary(
        string='Total', compute='_compute_amount', help="Total amount with taxes")

    inv_amount_paid = fields.Monetary(
        "Paid Amount", readonly=True, compute='_compute_amount')
    inv_amount_untaxed = fields.Monetary(
        string='Untaxed Amount', readonly=True, compute='_compute_amount')
    inv_amount_tax = fields.Monetary(
        string='Tax', readonly=True, compute='_compute_amount')
    inv_amount_total = fields.Monetary(
        string='Amount Total', readonly=True, compute='_compute_amount')

    partner_id = fields.Many2one('res.partner', string='Partner',
                                 related='related_id.partner_id', store=True, readonly=True, related_sudo=False)
    currency_id = fields.Many2one(
        'res.currency', related='related_id.currency_id', store=True, related_sudo=False)
    account_id = fields.Many2one('account.account', string='Account', default=_default_account, ondelete='restrict',
                                 required=True,  domain=[('deprecated', '=', False)], help="The partner account used for this invoice.")

    @api.onchange('invoice_id')
    @api.depends('invoice_id', 'inv_amount_total')
    def _onchange_invoice_ids(self):
        # if not self.name:
        #    warning = {
        #            'title': _('Warning!'),
        #            'message': _('First you must write a description!'),
        #        }
        #    return {'warning': warning}
        for line in self:
            if line.invoice_id:
                name = line.invoice_id.reference or line.invoice_id.number
                line.name = ("%s %s" %
                             (line.related_id.name or '', name or '')).strip()
                if not line.related_id.is_retention or not line.invoice_id.get_pe_data_by_code('PE.CPE.CATALOG23', '01'):
                    line.amount_unit = line.inv_amount_total
                    line.related_line_tax_ids = line.invoice_id.tax_line_ids.filtered(
                        lambda r: r.amount_total > 0).mapped('tax_id')
                else:
                    amount_unit = line.invoice_id.currency_id.round(line.inv_amount_paid * (
                        1/(1-line.invoice_id.get_pe_data_by_code('PE.CPE.CATALOG23', '01').value/100))) - line.inv_amount_paid
                    date_invoice = line.related_id.date_invoice or fields.Date.context_today(
                        self)
                    line.amount_unit = line.invoice_id.currency_id.with_context(
                        date=date_invoice).compute(amount_unit, line.related_id.currency_id)
        return {}

    # @api.multi
    @api.depends('invoice_id')
    def _compute_amount(self):
        for line in self:
            currency_id = line.related_id and line.related_id.currency_id or None
            amount_unit = line.amount_unit
            taxes = False
            if line.related_line_tax_ids:
                taxes = line.related_line_tax_ids.compute_all(
                    amount_unit, currency_id, line.quantity, product=None, partner=line.related_id.partner_id)
            amount_subtotal = taxes['total_excluded'] if taxes else amount_unit
            amount_total = taxes['total_included'] if taxes else amount_subtotal

            #inv_amount_paid = self.invoice_id.amount_paid
            inv_amount_untaxed = 0
            inv_amount_tax = 0
            inv_amount_total = 0
            inv_amount_paid = 0
            invoice_id = line.invoice_id
            l_inv_amount_untaxed = invoice_id.amount_untaxed
            l_inv_amount_tax = invoice_id.amount_tax
            l_inv_amount_total = invoice_id.amount_total
            l_inv_amount_paid = 0.0
            paids = json.loads(invoice_id.payments_widget or 'false')
            if paids:
                for paid in paids.get('content', []):
                    l_inv_amount_paid += paid.get('amount', 0)
            if line.related_id.currency_id != invoice_id.currency_id:
                inv_amount_paid += line.related_id.currency_id.with_context(
                    date=line.related_id.date_invoice).compute(l_inv_amount_paid, invoice_id.currency_id)
                inv_amount_untaxed += line.related_id.currency_id.with_context(
                    date=line.related_id.date_invoice).compute(l_inv_amount_untaxed, invoice_id.currency_id)
                inv_amount_tax += line.related_id.currency_id.with_context(
                    date=line.related_id.date_invoice).compute(l_inv_amount_tax, invoice_id.currency_id)
                inv_amount_total += line.related_id.currency_id.with_context(
                    date=line.related_id.date_invoice).compute(l_inv_amount_total, invoice_id.currency_id)
            else:
                inv_amount_paid += l_inv_amount_paid
                inv_amount_untaxed += l_inv_amount_untaxed
                inv_amount_tax += l_inv_amount_tax
                inv_amount_total += l_inv_amount_total

            if line.related_id.currency_id and line.related_id.currency_id != line.related_id.company_id.currency_id:
                #amount_subtotal = self.related_id.currency_id.with_context(date=self.related_id.date_invoice).compute(amount_subtotal, self.related_id.company_id.currency_id)
                amount_total = line.related_id.currency_id.with_context(
                    date=line.related_id.date_invoice).compute(amount_total, line.related_id.company_id.currency_id)
                #inv_amount_paid = self.related_id.currency_id.with_context(date=self.related_id.date_invoice).compute(inv_amount_paid, self.related_id.company_id.currency_id)
                #inv_amount_untaxed = self.related_id.currency_id.with_context(date=self.related_id.date_invoice).compute(inv_amount_untaxed, self.related_id.company_id.currency_id)
                #inv_amount_tax = self.related_id.currency_id.with_context(date=self.related_id.date_invoice).compute(inv_amount_tax, self.related_id.company_id.currency_id)
                #inv_amount_total = self.related_id.currency_id.with_context(date=self.related_id.date_invoice).compute(inv_amount_total, self.related_id.company_id.currency_id)

            line.inv_amount_untaxed = inv_amount_untaxed
            line.inv_amount_tax = inv_amount_tax
            line.inv_amount_total = inv_amount_total
            line.inv_amount_paid = inv_amount_paid
            line.amount_subtotal = amount_subtotal
            line.amount_total = amount_total
