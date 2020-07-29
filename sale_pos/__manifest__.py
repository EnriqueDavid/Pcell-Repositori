# -*- coding: utf-8 -*-
{
    'name': "Sale to POS",

    'summary': """
        Sale, Point of Sale""",

    'description': """
        Integrate Sale on Point Of Sale
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'sale',  
        'sale_management', 
        'sale_stock', 
        'point_of_sale',
        'pos_journal_sequence',
        'pos_refund',
        'account_annul'
    ],

    # always loaded
    'data': [
        'security/sale_pos_security.xml',
        'security/ir.model.access.csv',
        'wizard/sale_make_order_advance_views.xml',
        'views/sale_views.xml',
        'views/pos_order_view.xml',
        'views/pos_session_view.xml',
        'views/pos_config_view.xml',
    ],
}