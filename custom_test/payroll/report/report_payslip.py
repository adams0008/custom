# -*- coding:utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models


class PayslipCustomReport(models.AbstractModel):
    _name = "report.hr_payroll_ci.report_payslip"
    _description = "Rapport"

    def get_somme_rubrique(self, obj=None, code=""):
        payslip_obj = self.env["hr.payslip"].search(
            [("employee_id", "=", obj.employee_id.id)]
        )
        cpt = 0
        d = str(obj.date_to)
        date_compare = d[2:4]
        for payslip in payslip_obj:
            d = str(payslip.date_to)
            date_to = d[2:4]
            for line in payslip.line_ids:
                if (
                    line.salary_rule_id.code == code
                    and obj.date_to >= payslip.date_to
                    and date_to == date_compare
                ):
                    cpt += line.total
        return cpt

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env["hr.payslip"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "hr.payslip",
            "docs": payslips,
            "data": data,
            # "get_somme_rubrique": self.get_somme_rubrique,
        }
