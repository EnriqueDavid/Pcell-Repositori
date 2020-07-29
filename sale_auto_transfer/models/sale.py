# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.force_picking_done(order.picking_ids)
        return res
    
    def force_picking_done(self, picking_ids):
        for picking in picking_ids:
            contains_tracked_products = any([(product_id.tracking != 'none') for product_id in self.order_line.mapped('product_id')])
            if contains_tracked_products:
                picking.action_confirm()
            else:
                picking.action_assign()
            picking.force_assign()
            if not contains_tracked_products:
                picking.action_done()