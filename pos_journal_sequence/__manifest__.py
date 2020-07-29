# -*- coding: utf-8 -*-
{
    'name': "POS Journal Sequence",

    'summary': """
        Point Of Sale, Journal""",

    'description': """
         Add Point Of Sale journals and sequence
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    
    "category": "Point Of Sale",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/pos_journal_sequence_template.xml',
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
}
