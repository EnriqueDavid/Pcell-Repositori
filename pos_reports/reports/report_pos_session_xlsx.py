

from odoo import models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime

class ReportPosSessionXlsx(models.AbstractModel):
    _name = 'report.pos_reports.report_pos_session_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_workbook_options(self):
        return {'remove_timezone': True}

    def generate_xlsx_report(self, workbook, data, session_id):
        if len(session_id)!=1:
            raise ValidationError(_("The report of multiple sessions can not be made"))
        worksheet = workbook.add_worksheet(_('Session Report'))
        bold = workbook.add_format({'bold': True})
        date_time = fields.Datetime.context_timestamp(session_id, datetime.now())
        font_15 = workbook.add_format({'font_size': 15, 'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yy hh:mm:ss', 'align':'left'})
        float_format = workbook.add_format({'num_format': '0.00'})
        worksheet.merge_range('A1:B1', date_time, date_format)
        worksheet.write('D1', session_id.config_id.company_id.name)
        
        worksheet.write('A3', session_id.name, font_15)
        
        worksheet.write('A5', _("Responsible Person:"), bold)
        worksheet.write('A6', session_id.user_id.name)
        
        worksheet.write('A5', _("Responsible Person:"), bold)
        worksheet.write('A6', session_id.user_id.name)
        
        
        row = 1
        col = 0
        
        #for obj in session_id:
        #    
        #    bold = workbook.add_format({'bold': True})
        #    sheet.write(0, 0, obj.name, bold)