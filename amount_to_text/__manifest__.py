# -*- coding: utf-8 -*-
{
    'name': "Amount to Text Spanish",

    'summary': """
        Converts numbers to letters""",

    'description': """
        Convert numbers to letters in Spanish
    """,

    'author': "Flexxoone",
    'website': "http://www.flexxoone",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization/Spanish',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'account',
    ],

    # always loaded
    'data': [
        'data/res_currency_data.xml',
        'views/res_currency_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}