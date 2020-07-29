# -*- coding: utf-8 -*-
{
    'name': "Certificate Management",

    'summary': """
        Certificate Management""",

    'description': """
        Certificate Management
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
        'base',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/pe_certificate_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}