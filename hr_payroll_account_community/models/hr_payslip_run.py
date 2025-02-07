# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, _


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"


    def action_validate_payslips(self):
        """Validate all payslips in the batch run."""
        for payslip in self.slip_ids:
            payslip.action_payslip_done()
            self.close_payslip_run()
        self.message_post(body=_("All payslips in this batch have been validated."))
