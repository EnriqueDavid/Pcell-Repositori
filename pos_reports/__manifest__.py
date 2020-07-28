# -*- coding: utf-8 -*-
{
    'name': "POS Report",

    'summary': """
        POS Report""",

    'description': """
        POS Report
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale',
                'pos_journal_sequence',
                'sale_pos',
                #'report_xlsx',
                ],

    'data': [
        'reports/pos_session_report_template.xml',
        'reports/pos_order_report_template.xml',
        'reports/pos_report.xml',
    ],
}