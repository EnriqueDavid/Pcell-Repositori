# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import datetime

class AccountInvoice(models.Model):
    _inherit = "account.move"

    pe_stock_ids = fields.Many2many(comodel_name="stock.picking", string="Pickings", 
                                    compute ="_compute_pe_stock_ids", readonly=True, copy=False)
    pe_stock_name = fields.Char("Picking Number", compute ="_compute_pe_stock_ids", copy=False)

    
    def _compute_pe_stock_ids(self):
        for invoice in self:
            invoice_id = invoice.debit_origin_id or invoice.reversed_entry_id or invoice
            picking_ids =  invoice_id.invoice_line_ids.mapped('sale_line_ids').mapped('order_id').mapped('picking_ids') #self._cr.fetchall()
            pe_stock_ids = []
            numbers=[]
            for picking_id in picking_ids:
                if picking_id.state not in ['draft', 'cancel']: 
                    numbers.append(picking_id.name)
                    pe_stock_ids.append(picking_id.id)
            if numbers:
                if len(numbers)==1:
                    invoice_id.pe_stock_name=numbers[0]
                else:
                    invoice_id.pe_stock_name = " - ".join(numbers)
            invoice_id.pe_stock_ids = pe_stock_ids
    
class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    pack_lot_ids = fields.Many2many(comodel_name="stock.move.line", string="Lots/Serials", 
                                    compute ="_get_pack_lot_ids", readonly=True, copy=False)
    pack_lot_name = fields.Char("Lots/Serials Name", compute ="_get_pack_lot_ids")

    pe_move_id = fields.Many2one("account.move", string="Move", ondelete='set null')

    @api.model
    @api.depends("move_id.pe_stock_ids", 'product_id')
    def _get_pack_lot_ids(self):
        for line in self:
            if line.move_id.pe_stock_ids.mapped('move_line_ids').mapped('lot_id'):
                pack_lot_ids = line.move_id.pe_stock_ids.mapped('move_line_ids').filtered(lambda lot: lot.product_id == line.product_id)
                pack_lot_name=[]
                for pack_lot_id in pack_lot_ids:
                    name=""
                    if line.product_id.tracking=='serial':
                        name+="S/N. "
                    elif line.product_id.tracking=='lot':
                        name+="Lt. "
                    name+= (pack_lot_id.lot_id and pack_lot_id.lot_id.name or pack_lot_id.lot_name or "")+" "
                    if pack_lot_id.product_qty:
                        name+= "Cant. %s" % str(pack_lot_id.product_qty)
                    if pack_lot_id.lot_id.life_date:
                        name+= "FV. %s" % datetime.strptime(pack_lot_id.lot_id.life_date,'%Y-%m-%d %H:%M:%S').date().strftime('%d/%m/%Y')
                    pack_lot_name.append(name)
                line.pack_lot_name= pack_lot_name and "\n".join(pack_lot_name) or False
                line.pack_lot_ids = pack_lot_ids.ids
    
    @api.model
    def _pe_get_accounting_data_for_valuation(self):
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()

        acc_src = accounts_data['stock_input'].id

        acc_dest = accounts_data['stock_output'].id

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))
        if not acc_src:
            raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.display_name))
        if not acc_dest:
            raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.display_name))
        if not acc_valuation:
            raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation    
    
    @api.model
    def _pe_prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):

        self.ensure_one()

        valuation_amount = cost
        if self._context.get('forced_ref'):
            ref = self._context['forced_ref']
        else:
            ref = self.move_id.move_name
        
        debit_value = self.company_id.currency_id.round(valuation_amount)

        if self.company_id.currency_id.is_zero(debit_value):
            raise UserError(_("The cost of %s is currently equal to 0. Change the cost or the configuration of your product to avoid an incorrect valuation.") % (self.product_id.display_name,))
        credit_value = debit_value

        partner_id = (self.move_id.partner_id and self.env['res.partner']._find_accounting_partner(self.move_id.partner_id).id) or False
        debit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': ref,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
        }
        credit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': ref,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
        }
        res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference
            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
            price_diff_line = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
            res.append((0, 0, price_diff_line))
        return res
    
    @api.model
    def _pe_create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        self.ensure_one()
        AccountMove = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty)
        quantity = quantity if self.move_id.type in ['out_invoice', 'in_refund'] else -1 * quantity
        
        ref = self.move_id.move_name
        if self.env.context.get('force_valuation_amount'):
            if self.env.context.get('forced_quantity') == 0:
                ref = 'Revaluation of %s (negative inventory)' % ref
            elif self.env.context.get('forced_quantity') is not None:
                ref = 'Correction of %s (modification of past move)' % ref

        move_lines = self.with_context(forced_ref=ref)._pe_prepare_account_move_line(quantity, abs(self.value), credit_account_id, debit_account_id)
        if move_lines:
            date = self._context.get('force_period_date', self.move_id.date_invoice)
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': ref,
                'stock_move_id': self.id, #Cambiar
            })
            new_account_move.post()
    
    def pe_stock_account_entry_move(self):
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False

        if self.move_id.type in ['in_invoice', 'out_refund']:
            journal_id, acc_src, acc_dest, acc_valuation = self._pe_get_accounting_data_for_valuation()
            if self.move_id.type in ['out_refund']:  # goods returned from customer
                self._pe_create_account_move_line(acc_dest, acc_valuation, journal_id)
            else:
                self._pe_create_account_move_line(acc_src, acc_valuation, journal_id)

        # Create Journal Entry for products leaving the company
        if self.move_id.type in ['out_invoice', 'in_refund']:
            journal_id, acc_src, acc_dest, acc_valuation = self._pe_get_accounting_data_for_valuation()
            if self.move_id.type in ['in_refund']:  # goods returned to supplier
                self._pe_create_account_move_line(acc_valuation, acc_src, journal_id)
            else:
                self._pe_create_account_move_line(acc_valuation, acc_dest, journal_id)


                
        