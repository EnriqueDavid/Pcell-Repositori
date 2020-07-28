# -*- coding: utf-8 -*-
from datetime import datetime
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    interpolated_prefix = fields.Char(
        "Interpolated Prefix", compute="compute_prefix_suffix")
    interpolated_suffix = fields.Char(
        "Interpolated Suffix", compute="compute_prefix_suffix")
    all_number_increment = fields.Integer(
        "Number Increment", compute="compute_prefix_suffix")

    def _get_prefix_suffix_char(self):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(
                pytz.timezone(self._context.get('tz') or 'UTC'))
            if self._context.get('ir_sequence_date'):
                effective_date = datetime.strptime(
                    self._context.get('ir_sequence_date'), '%Y-%m-%d')
            if self._context.get('ir_sequence_date_range'):
                range_date = datetime.strptime(self._context.get(
                    'ir_sequence_date_range'), '%Y-%m-%d')

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            res = {}
            for key, format in sequences.items():
                res[key] = effective_date.strftime(format)
                res['range_' + key] = range_date.strftime(format)
                res['current_' + key] = now.strftime(format)

            return res

        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except ValueError:
            raise UserError(
                _('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))
        return interpolated_prefix, interpolated_suffix

    @api.depends('number_next_actual', 'number_next')
    def compute_prefix_suffix(self):
        for sequence in self:
            interpolated_prefix, interpolated_suffix = sequence._get_prefix_suffix_char()
            sequence.interpolated_prefix = interpolated_prefix
            sequence.interpolated_suffix = interpolated_suffix
            if not sequence.use_date_range:
                sequence.all_number_increment = sequence.number_next_actual
            else:
                dt = fields.Date.today()
                seq_date = sequence.env['ir.sequence.date_range'].search(
                    [('sequence_id', '=', sequence.id), ('date_from', '<=', dt), ('date_to', '>=', dt)], limit=1)
                if not seq_date:
                    seq_date = sequence._create_date_range_seq(dt)
                sequence.all_number_increment = seq_date.number_next

    def pos_next_by_number(self, number):
        num = number
        interpolated_prefix, interpolated_suffix = self._get_prefix_suffix_char()
        if interpolated_prefix:
            number = number[len(interpolated_prefix):]
        if interpolated_suffix:
            number = number[:-1*len(interpolated_suffix)]
        try:
            number_next_actual = int(number)+1
            self.pos_next(number_next_actual)
        except:
            raise UserError(_('Invalid number for sequence \'%s\'') % (num))

    def pos_next(self, number_next_actual):
        if not self.use_date_range and self.number_next_actual < number_next_actual:
            limit = self.number_next_actual - number_next_actual
            if limit >= 100:
                raise UserError(_('Invalid number for sequence'))
            self.sudo().number_next_actual = number_next_actual
        elif self.all_number_increment < number_next_actual:
            dt = fields.Date.today()
            seq_date = self.env['ir.sequence.date_range'].search(
                [('sequence_id', '=', self.id), ('date_from', '<=', dt), ('date_to', '>=', dt)], limit=1)
            if not seq_date:
                seq_date = self._create_date_range_seq(dt)
            limit = seq_date.number_next - number_next_actual
            if limit >= 100:
                raise UserError(_('Invalid number for sequence'))
            seq_date.sudo().number_next = number_next_actual

    def pos_get_sync_number(self, number_next_actual=None):
        if number_next_actual:
            self.pos_next(number_next_actual)
        number = self.sudo().next_by_id()
        num = number
        interpolated_prefix, interpolated_suffix = self._get_prefix_suffix_char()
        if interpolated_prefix:
            number = number[len(interpolated_prefix):]
        if interpolated_suffix:
            number = number[:-1*len(interpolated_suffix)]
        try:
            number_actual = int(number)
        except:
            raise UserError(_('Invalid number for sequence \'%s\'') % (num))
        return {'number': num, 'invoice_sequence_number': number_actual}
