# -*- coding: utf-8 -*-
{
    'name': "Peruvian docs validators",

    'summary': """
        Validate RUC and DNI
        """,

    'description': """
    Este addon valida el ruc de los clientes con la SUNAT
    
    """,

    'author': "Flexxoone",
    'website': "www.flexxoone",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization/Peruvian',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_vat', 
        'l10n_pe_datas',
        'l10n_pe',
        #'l10n_pe_toponyms',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/res_city_data.xml',
        'data/l10n_pe_district.xml',
        'views/res_partner_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
