# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    session_id = fields.Many2one(
        'pos.session', string='Session', readonly=True, copy=False)
    pos_order_id = fields.Many2one('pos.order', string='POS Order', readonly=True, copy=False)
    pos_order_count = fields.Integer(
        "Order Count", compute="_compute_pos_order_count", default=0)
    
    @api.depends('pos_order_id')
    def _compute_pos_order_count(self):
        for sale in self:
            sale.pos_order_count = len(sale.pos_order_id)
    
    def action_view_pos_order(self):
        pos_order_id = self.pos_order_id
        action = self.env.ref('point_of_sale.action_pos_pos_form').read()[0]
        if len(pos_order_id) > 1:
            action['domain'] = [('id', 'in', pos_order_id.ids)]
        elif len(pos_order_id) == 1:
            action['views'] = [(self.env.ref(
                'point_of_sale.view_pos_pos_form').id, 'form')]
            action['res_id'] = pos_order_id.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    def prepare_pos_order(self):
        self.ensure_one()
        order_vals = {
            'name': self.name,
            'user_id': self.user_id and self.user_id.id,
            'session_id':   self.session_id.id, # Crear
            'pos_reference': self.name,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (
                self.fiscal_position_id.id or
                self.partner_invoice_id.property_account_position_id.id),
            'pricelist_id': self.pricelist_id.id,
            'note': self.note,
            'payment_term_id': self.payment_term_id.id,
            'company_id': self.company_id.id,
            'team_id': self.team_id.id,
            'picking_id': self.picking_ids and self.picking_ids[-1].id or False,
            'sale_order_id': self.id,
            'amount_tax': self.amount_tax,
            'amount_total': self.amount_total,
            'amount_paid': self.amount_total,
            'amount_return':0,
        }
        return order_vals

    def action_pos_order_create(self):
        for order_id in self:
            vals = order_id.prepare_pos_order()
            lines = []
            for line_id in order_id.order_line:
                lines.append((0, 0, line_id.prepare_pos_order_line()))
            vals['lines']=lines
            pos_order_id = self.env['pos.order'].sudo().create(vals)
            order_id.pos_order_id = pos_order_id.id

 
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line' 
    
    def prepare_pos_order_line(self):
        self.ensure_one()
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.product_id.taxes_id.compute_all(price, self.order_id.pricelist_id.currency_id, self.product_uom_qty, product=self.product_id, partner=False)  
        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'price_unit': self.price_unit,
            'price_subtotal':self.price_subtotal,
            'price_subtotal_incl': self.price_total,
            'qty': self.product_uom_qty,
            'discount': self.discount,
            'product_id': self.product_id.id or False,
            #'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'order_line_id':self.id
            #'account_analytic_id': self.order_id.analytic_account_id.id,
            #'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res
