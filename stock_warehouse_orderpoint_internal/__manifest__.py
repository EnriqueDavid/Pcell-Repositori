# -*- coding: utf-8 -*-
{
    'name': "Stock Warehouse Order Point Internal",

    'summary': """
        Create Internal Transfer""",

    'description': """
        Create Internal Transfer
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'procurement'],

    # always loaded
    'data': [
        'views/stock_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}