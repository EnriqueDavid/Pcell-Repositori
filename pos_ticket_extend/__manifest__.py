# -*- coding: utf-8 -*-
{
    'name': "POS Ticket Extend",

    'summary': """
        Point Of Sale, Ticket""",

    'description': """
        Point Of Sale Partner details on the ticket
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    'category': 'Point Of Sale',
    'version': '0.1',

    'depends': ['point_of_sale'],

    'data': [
        'views/pos_ticket_template.xml',
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
}