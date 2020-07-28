# -*- coding: utf-8 -*-
{
    'name': "Peruvian Stock",

    'summary': """
        Peruvian Stock""",

    'description': """
        Peruvian Stock
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    'category': 'Uncategorized',
    'version': '0.2',
    'depends': [
        'account', 
        'stock',
        'product_expiry',
    ],

    'data': [
        #'views/report_invoice.xml',
        'report/report_picking.xml',
        'views/product_view.xml',
        'views/stock_view.xml',
    ],
}