# -*- coding: utf-8 -*-
{
    'name': "Peruvian Invoice",

    'summary': """
        Peruvian Invoice""",

    'description': """
        Peruvian Invoice
    """,

    'author': "Flexxoone",
    'website': "http://www.flexxoone",

    'category': 'Uncategorized',
    'version': '0.2',
    'depends': [
        'account', 
        'sale',
        'l10n_pe_vat',
    ],
    'data': [
        'security/invoice_security.xml',
        'wizard/account_invoice_debit_view.xml',
        #'wizard/pe_related_invoice_wizard_view.xml',
        'views/account_view.xml',
        # 'views/account_move_view.xml',
        'views/company_view.xml',
        'views/product_view.xml',
        'views/report_invoice.xml',
        'views/currency_view.xml'
    ],
}