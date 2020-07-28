# -*- coding: utf-8 -*-
{
    'name': "Account Move Target",

    'summary': """
        Account,Target""",

    'description': """
        Move target
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_view.xml',
    ],
}