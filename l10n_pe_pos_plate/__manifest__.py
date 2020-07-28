
# -*- coding: utf-8 -*-
##############################################################################
{
    'name': 'Pos CPE Plate',
    'summary': """POS CPE """,
    'version': '11.0.1.0',
    'description': """Point Of Sale""",
    'author': 'Flexxoone, Odoo 11',
    'company': 'Flexxoone, Odoo 11',
    'website': 'http://www.flexxoone',
    'license': 'LGPL-3',
    'category': 'Base',
    'depends': ['account', 'sale', 'point_of_sale',
                'l10n_pe_pos_cpe', 'sale_pos'],
    'data': [
        #'views/product_view.xml',
        'views/template.xml',
      ],
    'demo': [],
    'installable': True,
    'qweb': ['static/src/xml/*.xml'],
    'auto_install': False,

}
