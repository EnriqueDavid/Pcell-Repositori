# -*- coding: utf-8 -*-
{
    'name': "Sale Report",

    'summary': """
        Sale, Report, Partner, Salesman""",

    'description': """
        Report Sale
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'sale_margin'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/sale_report_wizard_view.xml',
        'views/report_sale_order.xml',
        'views/sale_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}