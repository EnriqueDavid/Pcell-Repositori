# -*- coding: utf-8 -*-

import base64
from odoo import fields, models, api, tools, _
from odoo.modules import get_module_resource
from odoo.exceptions import ValidationError, UserError

standard_template = [
    ('advanced', 'Advanced'),
    ('custom', 'Contemporary'),
    ('creative', 'Creative'),
    ('elegant', 'Elegant'),
    ('exclusive', 'Exclusive'),
    ('incredible', 'Incredible'),
    ('innovative', 'Innovative'),
    ('professional', 'Professional'),
]

template = {
    'custom': {
        'theme_color': '#a24689',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#a24689',
    },
    'elegant': {
        'theme_color': '#eb5554',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#eb5554',
    },
    'creative': {
        'theme_color': '#0692C3',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#0692C3',
    },
    'professional': {
        'theme_color': '#FF6340',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#FF6340',
    },
    'advanced': {
        'theme_color': '#3D50A5',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#3D50A5',
    },
    'exclusive': {
        'theme_color': '#46A764',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#46A764',
    },
    'incredible': {
        'theme_color': '#0692C3',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#0692C3',
    },
    'innovative': {
        'theme_color': '#0692C3',
        'theme_text_color': '#FFFFFF',
        'text_color': '#000000',
        'company_color': '#6F8192',
        'customer_color': '#000000',
        'company_address_color': '#6F8192',
        'customer_address_color': '#000000',
        'odd_party_color': '#FFFFFF',
        'even_party_color': '#e6e8ed',
        'watermark_text_color': '#0692C3',
    },
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _default_report_template(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), (
            'report_name', '=', 'sistemerp_ereport_template.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search(
                [('model', '=', 'account.move')])[0]
        return report_id

    @api.depends('partner_id')
    def _default_report_template1(self):
        report_obj = self.env['ir.actions.report']
        report_id = report_obj.search([('model', '=', 'account.move'), (
            'report_name', '=', 'sistemerp_ereport_template.report_invoice_template_custom')])
        if report_id:
            report_id = report_id[0]
        else:
            report_id = report_obj.search(
                [('model', '=', 'account.move')])[0]
        if self.report_template_id and self.report_template_id.id < report_id.id:
            self.write(
                {'report_template_id': report_id and report_id.id or False})
            #self.report_template_id = report_id and report_id.id or False
        self.report_template_id1 = report_id and report_id.id or False

    @api.model
    def _get_default_image(self, is_company, colorize=False):
        img_path = get_module_resource(
            'sistemerp_ereport_template', 'static/src/img', 'avatar.png')
        with open(img_path, 'rb') as f:
            image = f.read()

        # colorize user avatars
        if not is_company:
            image = tools.image_colorize(image)

        return tools.image_resize_image_big(base64.b64encode(image))

    @api.onchange('standard_template')
    def _onchange_invoice_template(self):
        if self.standard_template:
            template_value = template.get(str(self.standard_template))
            self.theme_color = template_value.get('theme_color', '#000000')
            self.theme_text_color = template_value.get(
                'theme_text_color', '#FFFFFF')
            self.text_color = template_value.get('text_color', '#000000')
            self.company_color = template_value.get('company_color', '#000000')
            self.company_address_color = template_value.get(
                'company_address_color', '#000000')
            self.customer_color = template_value.get(
                'customer_color', '#000000')
            self.customer_address_color = template_value.get(
                'customer_address_color', '#000000')
            self.odd_party_color = template_value.get(
                'odd_party_color', '#000000')
            self.even_party_color = template_value.get(
                'even_party_color', '#000000')
            self.watermark_text_color = template_value.get(
                'watermark_text_color', '#000000')
        return

    def _get_font(self):
        return self.env['report.fonts'].search([('family', '=', 'Helvetica'), ('mode', '=', 'all')], limit=1)

    def act_discover_fonts(self):
        self.ensure_one()
        return self.env["report.fonts"].font_scan()

    theme_color = fields.Char(string="Template Base Color", required=True,
                              help="Please set Hex color for Template.", default="#a24689")
    theme_text_color = fields.Char(string="Template Text Color", required=True,
                                   help="Please set Hex color for Template Text.", default="#FFFFFF")
    text_color = fields.Char(string="General Text Color", required=True,
                             help="Please set Hex color for General Text.", default="#000000")
    company_color = fields.Char(string="Company Name Color", required=True,
                                help="Please set Hex color for Company Name.", default="#6F8192")
    customer_color = fields.Char(string="Customer Name Color", required=True,
                                 help="Please set Hex color for Customer Name.", default="#000000")
    company_address_color = fields.Char(string="Company Address Color", required=True,
                                        help="Please set Hex color for Company Address.", default="#6F8192")
    customer_address_color = fields.Char(string="Customer Address Color", required=True,
                                         help="Please set Hex color for Customer Address.", default="#000000")
    odd_party_color = fields.Char(string="Table Odd Parity Color", required=True,
                                  help="Please set Hex color for Table Odd Parity.", default="#FFFFFF")
    even_party_color = fields.Char(string="Table Even Parity Color", required=True,
                                   help="Please set Hex color for Table Even Parity.", default="#e6e8ed")
    report_template_id1 = fields.Many2one('ir.actions.report', string="Invoice Template1", compute='_default_report_template1',
                                          help="Please select Template report for Invoice", domain=[('model', '=', 'account.move')])
    report_template_id = fields.Many2one('ir.actions.report', string="Invoice Template", default=_default_report_template,
                                         help="Please select Template report for Invoice", domain=[('model', '=', 'account.move')])
    invoice_logo = fields.Binary("Report Logo", attachment=True, required=True, default=lambda self: self._get_default_image(False, True),
                                 help="This field holds the image used as Logo for Invoice template report")
    is_description = fields.Boolean(string="Display Product Description", default=True,
                                    help="Please check it if you want to show product description in report.")
    watermark_logo = fields.Binary("Report Watermark Logo", default=lambda self: self._get_default_image(
        False, True), help="Please set Watermark Logo for Report.")
    is_company_bold = fields.Boolean(string="Display Company Name in Bold", default=True,
                                     help="Please check it if you want to show Company Name in Bold.")
    is_customer_bold = fields.Boolean(string="Display Customer Name in Bold", default=False,
                                      help="Please check it if you want to show Customer Name in Bold.")
    is_show_invoice_notes = fields.Boolean(
        string="Display Invoice Notes", default=False, help="Please check it if you want to show Invoice Notes in pdf.")
    is_show_payment_notes = fields.Boolean(
        string="Display Payment Term", default=False, help="Please check it if you want to show Payment Term in pdf.")
    is_show_payment_description = fields.Boolean(
        string="Display Payment Description", default=False, help="Please check it if you want to show Payment Description in pdf.")
    standard_template = fields.Selection(standard_template, string="Standard Template Configuration", required=True,
                                         default='custom', help="Please select your choice Standard Color Configuration for all Template.")

    is_show_watermark = fields.Boolean(string="Display Watermark?", help="Please check if want to display watermark")

    watermark = fields.Selection(selection=[('logo', 'Logo'), ('text', 'Text'), ('status', 'Status')], required=True,
                                 string="Display Watermark", default='text',
                                 help='We can choose watermark for pdf either logo or text or status.')
    watermark_text = fields.Char(string="Watermark Text",
                                 default='Documento sin valor Legal.', help="Please enter watermark text")
    watermark_text_font_size = fields.Integer(
        'Watermark Text Font Size(em)', default=6, help="Please set watermark text font size")
    watermark_text_color = fields.Char(string="Watermark Text Color", required=[(
        'watermark', '!=', 'logo')], help="Please set Hex color for Watermark text.", default="#a24689")
    add_product_image = fields.Boolean(
        string="Display Product Image", default=False, help="Please check it if you want to show Product Image in pdf.")

    font_id = fields.Many2one(comodel_name='report.fonts', string="Report Font", default=lambda self: self._get_font(),
                              domain=[
        ('mode', 'in', ('Normal', 'Regular', 'all', 'Book'))],
        help="Set the font into the report header, it will be used as default font in the clever reports of the user company")
    font_size = fields.Integer('Report Font Size(px)', default=12,
                               required=True, help="Please define report font size")

    is_show_signature = fields.Boolean(
        string='Display Signature', default=False, help="Please check it if you want to show signature in PDF.")
    signature = fields.Binary(string="Signature", default=lambda self: self._get_default_image(
        False, True), help="Please upload signature image to display in report.")
    report_footer_selection = fields.Selection(selection=[('standard', 'Standard'), ('multi_columns', 'Multi Columns Footer')], default='standard',
                                               string="Display Report Footer", help="Select footer style if you want to show in report",)
    logo_footer = fields.Binary("Report Footer Logo", compute='_compute_logo_footer',
                                store=True, help="Please set Footer Logo for Report.")
    is_show_bank_details = fields.Boolean(
        string='Display Bank Details', default=False, help="Please check it if you want to show Bank details in pdf.")
    report_bank_id = fields.Many2one('res.partner.bank', string="Banks",
                                     help="Please select bank account which you want to show Bank details in pdf.")
    is_show_barcode = fields.Boolean(string='Display Report Barcode', default=True,
                                     help="Please check it if you want to show report barcode in pdf.")
    add_amount_in_words = fields.Boolean(
        string="Display Amount In Word", default=True, help="Please unchecked if you want to hide amount in words")

    add_product_image = fields.Boolean(
        string="Display Product Image", default=False, help="Please check it if you want to show Product Image in pdf.")

    def action_view_report_extra_content(self):
        action = self.env.ref(
            'sistemerp_ereport_template.action_report_extracontent').read()[0]
        action['domain'] = [('company_id', '=', self.id)]
        return action

    @api.depends('partner_id', 'partner_id.image_1920')
    def _compute_logo_footer(self):
        for company in self:
            company.logo_footer = company.partner_id.image_1920

    @api.constrains('font_size', 'watermark_text_font_size')
    def check_font_size(self):
        if self.watermark_text_font_size <= 0 or self.watermark_text_font_size > 10:
            raise ValidationError(
                _('Please input watermark text font size is greater than 0 and lower than 10, otherwise your report will very massive.'))
        if self.font_size <= 10 or self.font_size >= 25:
            raise ValidationError(
                _('Please input font size is greater than 10 and lower than 25, otherwise your report will very massive.'))
