# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    cargo_cost = fields.Float("Flete", digits=(16,2))
    total_weight = fields.Float("Peso Total", digits=dp.get_precision('Stock Weight'), compute = "compute_total_weight")
    cargo_cost_compute = fields.Float("Total Flete", digits=(16,2), compute="comp_cargo_cost_compute")
    
    @api.multi
    def comp_cargo_cost_compute(self):
        for order_id in self:
            cargo_cost_compute = 0 
            for line in order_id.order_line:
                cargo_cost_compute+=line.cargo_cost
            order_id.cargo_cost_compute = cargo_cost_compute
    
    @api.multi
    def compute_total_weight(self):
        for order_id in self:
            total_weight = 0
            for line in order_id.order_line:
                total_weight+=line.product_id.weight*line.product_qty
            order_id.total_weight = total_weight

    @api.depends('cargo_cost')
    @api.onchange('cargo_cost', 'price_unit')
    def onchange_cargo_cost(self):
        if self.cargo_cost >0:
            unit_cost_cargo = self.total_weight/self.cargo_cost
            for line in self.order_line:
                if not line.unit_cost_cargo:
                    if not self.invoice_ids.filtered(lambda inv: inv.state not in ['draft','annul','cancel']):
                        dtm = fields.Datetime.from_string(self.date_order)
                        date = fields.Date.to_string(dtm)
                    else:
                        date = self.invoice_ids.filtered(lambda inv: inv.state not in ['draft','annul','cancel'])[0].date
                    context = {'date': date}
                    line.unit_cost_cargo = unit_cost_cargo
                    price_unit = self.currency_id.with_context(**context).compute(line.price_unit, self.company_id.currency_id, False)
                    price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=self.currency_id, quantity=1.0, product=line.product_id, partner=self.partner_id)['total_included']
                    line.cargo_cost = line.product_id.weight*line.unit_cost_cargo
                    line.price_unit_cargo_cost = price_unit + line.unit_cost_cargo
                    

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    #total_weight = fields.Float("Peso Total", digits=dp.get_precision('Stock Weight'), compute = "compute_total_weight")
    unit_kg_cargo = fields.Float("Cost. Kg Flete", digits=(16,4))
    unit_cost_cargo = fields.Float("Cost. Un. Flete", digits=(16,4))
    cargo_cost = fields.Float("Costo Total de Flete", digits=(16,4))
    price_unit_cargo_cost = fields.Float("Costo Un. + Flete", digits=(16,4))
    
    @api.multi
    def compute_unit_cost_cargo(self):
        for line in self:
            self.cargo_cost = self.product_id.weight*self.unit_cost_cargo
    
    @api.onchange('unit_kg_cargo', 'price_unit','product_qty', 'pe_has_refund')
    def onchange_unit_cost_cargo(self):
        if self.unit_kg_cargo:
            if not self.order_id.invoice_ids.filtered(lambda inv: inv.state not in ['draft','annul','cancel']):
                dtm = fields.Datetime.from_string(self.order_id.date_order)
                date = fields.Date.to_string(dtm)
            else:
                date = self.order_id.invoice_ids.filtered(lambda inv: inv.state not in ['draft','annul','cancel'])[0].date
            context = {'date': date}
            price_unit = self.order_id.currency_id.with_context(**context).compute(self.price_unit, self.order_id.company_id.currency_id, False)
            
            price_unit = self.taxes_id.with_context(round=False).compute_all(price_unit, currency=self.order_id.currency_id, quantity=1.0, product=self.product_id, partner=self.order_id.partner_id)['total_included']
            self.unit_cost_cargo = self.product_id.weight*self.unit_kg_cargo
            self.price_unit_cargo_cost = price_unit + self.unit_cost_cargo
    
    
    #@api.multi
    #def compute_total_weight(self):
    #    for line in self:
    #        line.total_weight = line.product_id.weight*line.product_qty
        
    
