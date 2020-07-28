# -*- encoding: utf-8 -*-

{
    "name": "Account Annul",
    "version": "1.0",
    "description": """
Manage the Annulation of Account Moves
======================================

The financial reports required inform about the annulled invoices and account moves.

Key Features
------------
* Add annul button on invoices
* Add annul button on account moves
    """,
    "author": "Cubic ERP",
    "website": "http://sistemERP.com",
    "category": "Financial",
    "depends": [
        "account",
        ],
    "data":[
        "views/account_view.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    'price': 20,
    'currency': 'USD',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
