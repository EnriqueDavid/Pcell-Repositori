# -*- coding: utf-8 -*-
{
    'name': "Peruvian POS CPE",

    'summary': """
        POS, CPE""",

    'description': """
        Peruvian Management POS CPE
    """,

    'author': "Flexxoone",
    'website': "http://www.flexxoone",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization/Peruvian',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'point_of_sale',
        'sale_pos',
        'l10n_pe_cpe',
        'l10n_pe_pos',
        'pos_refund',
    ],

    # always loaded
    'data': [
        'wizard/sale_make_order_advance_views.xml',
        'wizard/pos_recover_wizard_view.xml',
        'views/l10n_pe_pos_cpe_templates.xml',
        'views/pos_order_view.xml',
        'views/pos_config_view.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml'
    ],
}