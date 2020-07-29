from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    annul = fields.Boolean('Annulled', readonly=True)
    state = fields.Selection(selection_add=[
        ('annul', 'Anulled'),
    ],
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' status is used when the invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Anulled' status is used when user annul invoice (keeping the invoice number).\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    def button_annul(self):
        self.button_cancel()
        self.write({'annul': True, 'state': 'annul'})
        return True


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"
    _description = "Accoun Invoice report"

    state = fields.Selection(selection_add=[('annul', 'Anulled')])
