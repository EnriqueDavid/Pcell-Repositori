# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round

class PosOrder(models.Model):
    _inherit = "pos.order"
    
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, 
                                          states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                          help="Delivery address for current sales order.")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    team_id = fields.Many2one('crm.team', 'Sales Channel')
    sale_order_id = fields.Many2one('sale.order', string='Order Reference', copy=False)
    pos_user_id = fields.Many2one(
        comodel_name='res.users', string='POS Salesman',
        help="Person who uses the cash register. It can be a reliever, a student or an interim employee.",
        default=lambda self: self.env.uid,
        states={'done': [('readonly', True)], 'invoiced': [('readonly', True)]})
    
    @api.constrains("sale_order_id")
    def check_sale_order_id(self):
        for order in self:
            if order.sale_order_id:
                if self.search_count([('sale_order_id','=', order.sale_order_id.id)])>1:
                    raise ValidationError(_('Sale Order already exists and violates unique field constrain'))
    
    def invoice_print(self):
        return self.account_move.action_invoice_print()

    def action_invoice_sent(self):
        res = self.account_move.sudo().action_invoice_sent()
        res['context']['res_id'] = res['context'].pop('default_res_id', False)
        return res
    
    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        res['invoice_origin'] = self.sale_order_id.name or self.name
        res['partner_shipping_id'] = self.partner_shipping_id.id
        res['invoice_payment_term_id'] = self.payment_term_id.id
        res['fiscal_position_id'] = self.fiscal_position_id
        res['team_id'] = self.team_id.id
        if not res.get('name') and res.get('type') == 'out_refund':
            res['name'] = '/'
        return res

    def _prepare_invoice_line(self, line):
        res = super()._prepare_invoice_line(line)
        res.update({
            'sequence': line.sequence,
        })
        if self.sale_order_id:
            res['sale_line_ids'] = [(6, 0, [line.order_line_id.id])]
        return res

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"
    
    tax_ids = fields.Many2many('account.tax', readonly=False)
    sequence = fields.Integer(string='Sequence', default=10, readonly=True)
    origin = fields.Char(string='Source Document', readonly=True)
    #layout_category_id = fields.Many2one('sale.layout_category', string='Section', readonly=True)
    order_line_id = fields.Many2one('sale.order.line', string='Order Lines', readonly=True)
    #analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    
