# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2020 yoboue.alla@gmail.com
##############################################################################
from odoo import api, models, _
from ..tools import format_amount


class ReportPayroll(models.AbstractModel):
    _name = 'report.payroll_raport.report_payroll'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.payslip'].search([
            ('date_from', '>=', data['form']['date_from']),
            ('date_to', '<=', data['form']['date_to'])
        ])

        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'data': data,
        }