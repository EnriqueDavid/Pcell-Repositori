# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models, tools, _
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    standard_name = fields.Char("Standard Name")
    

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    standard_name = fields.Char("Standard Name", related="product_tmpl_id.standard_name")
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            products = self.env['product.product']
            if operator in positive_operators:
                products = self.search([('default_code', '=', name)] + args, limit=limit)
                if products:
                    names=products.mapped("standard_name")
                    if names:
                        products=self.search(["|",('id', 'in', products.ids),('standard_name', "in", names)] + args, limit=limit)
                if not products:
                    products = self.search([('barcode', '=', name)] + args, limit=limit)
            if not products and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                products = self.search(args + [('default_code', operator, name)], limit=limit)
                if products:
                    names=products.mapped("standard_name")
                    if names:
                        products=self.search(["|",('id', 'in', products.ids),('standard_name', "in", names)] + args, limit=limit)
                if not limit or len(products) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(products)) if limit else False
                    products += self.search(args + ["|",('name', operator, name),('standard_name', operator, name),('id', 'not in', products.ids)], limit=limit2)
            elif not products and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                products = self.search(domain, limit=limit)
            if not products and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    products = self.search([('default_code', '=', res.group(2))] + args, limit=limit)
                    if products:
                        names=products.mapped("standard_name")
                        if names:
                            products=self.search(["|",('id', 'in', products.ids),('standard_name', "in", names)] + args, limit=limit)
            # still no results, partner in context: search on supplier info as last hope to find something
            if not products and self._context.get('partner_id'):
                suppliers = self.env['product.supplierinfo'].search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)])
                if suppliers:
                    products = self.search([('product_tmpl_id.seller_ids', 'in', suppliers.ids)], limit=limit)
        else:
            products = self.search(args, limit=limit)
        return products.name_get()
    
    #@api.model
    #def name_search(self, name='', args=None, operator='ilike', limit=100):
    #    args = args or []
    #    if name:
            #domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
    #        product =self.search([('standard_name','!=',False),('standard_name', operator, name)], limit=limit)
    #        if product:
    #            domain=["|",("id","in", product.ids)]
    #            args = domain+args
    #    res = super(ProductProduct, self).name_search(name=name, args=args, operator=operator, limit=limit)
    #    return res