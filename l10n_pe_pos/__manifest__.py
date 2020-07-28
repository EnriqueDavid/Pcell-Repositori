# -*- coding: utf-8 -*-
{
    'name': "Peruvian POS",

    'summary': """
        Peruvian Management POS""",

    'description': """
        Peruvian Management POS
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
        'amount_to_text',
        'pos_journal_sequence',
        'l10n_pe_vat',
        'pos_ticket_extend',
    ],

    # always loaded
    'data': [
        'views/l10n_pe_pos_templates.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml'
    ],
}
