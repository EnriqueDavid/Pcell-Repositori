# -*- coding: utf-8 -*-
{
    'name': "Peru - Accounting Extend",

    'summary': """
        Account, TAx""",

    'description': """
        Peruvian accounting chart and tax localization.
    """,

    'author': "Flexxoone",
    'website': "http://www.flexxoone",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_pe'],

    # always loaded
    'data': [
        'data/account_data.xml',
        'data/l10n_pe_chart_data.xml',
        # 'data/account_tax_data.xml',
    ],
}