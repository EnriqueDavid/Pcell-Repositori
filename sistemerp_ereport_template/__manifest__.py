# -*- coding: utf-8 -*-

{
    'name': 'Multiple Invoice Template',
    'version': '13.0.1.0.2',
    'author': 'Flexxoone',
    'license': 'OPL-1',
    'category': 'Accounting',
    'depends': ['account', 'sale_management', 'purchase'],
    'website': 'https://www.flexxoone',
    'description': '''Multiple Invoice Templates ,  
    ''',
    'summary': '¡Diversas plantillas de facturas a un solo Clic!',
    'data': [
        'security/ir.model.access.csv',
        'data/template_data.xml',
        'views/web_widget_color_view.xml',
        'views/templates.xml',
        'views/template_report.xml',
        'views/creative_template.xml',
        'views/elegant_template.xml',
        'views/professional_template.xml',
        'views/exclusive_template.xml',
        'views/advanced_template.xml',
        'views/incredible_template.xml',
        'views/innovative_template.xml',
        'views/custom_template.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/invoice_view.xml',
        'views/report_extra_content_view.xml',
        'views/invoice_report_templates.xml',
    ],
    'qweb': [
        'static/src/xml/widget_color.xml',
    ],
    'external_dependencies': {
        'python': ['img2pdf', 'fpdf','num2words']
    },
    'images': ['static/description/splash-screen.png'],
    'installable': True,
    'auto_install': False,
    'web_preload': True,
}
