# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrPayslipRun(models.Model):
    _name = "hr.payslip.run"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Payslip Batches"
    _order = "id desc"

    name = fields.Char(required=True, readonly=True)
    slip_ids = fields.One2many(
        "hr.payslip",
        "payslip_run_id",
        string="Payslips",
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("verify", "En attente"), ("close", "Fermé")],
        string="Status",
        index=True,
        readonly=True,
        copy=False,
        tracking=1,
        default="draft",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    date_start = fields.Date(
        string="Date From",
        required=True,
        readonly=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_end = fields.Date(
        string="Date To",
        required=True,
        readonly=True,
        default=lambda self: fields.Date.today().replace(day=1)
        + relativedelta(months=+1, day=1, days=-1),
    )
    credit_note = fields.Boolean(
        readonly=True,
        help="If its checked, indicates that all payslips generated from here "
        "are refund payslips.",
    )
    struct_id = fields.Many2one(
        "hr.payroll.structure",
        string="Structure",
        readonly=True,
        help="Defines the rules that have to be applied to this payslip batch, "
        "accordingly to the contract chosen. If you let empty the field "
        "contract, this field isn't mandatory anymore and thus the rules "
        "applied will be all the rules set on the structure of all contracts "
        "of the employee valid for the chosen period",
    )
    from_payslip_run = fields.Boolean(
        string="From_payslip_run", required=False, default=True
    )

    payslip_count = fields.Integer('Fiche de paie', compute="method_payslip_count")

    def method_payslip_count(self):
        for record in self:
            record.payslip_count = len(record.slip_ids)

    def draft_payslip_run(self):
        self.write({"state": "draft"})
        for slip in self.slip_ids:
            slip.write({'state': 'draft'})
            if slip.move_id:
                slip.move_id.unlink()
    

    def close_payslip_run(self):
        return self.write({"state": "close"})
    

    def compute_sheet_run(self):
        self.write({"state": "verify"})
        for slip in self.slip_ids:
            slip.compute_sheet()
    
    def _are_payslips_ready(self):
        return all(slip.state in ['done', 'cancel'] for slip in self.mapped('slip_ids'))
    

    def action_open_payslips(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.payslip",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.slip_ids.ids]],
            "context": {'default_payslip_run_id': self.id},
            "name": "Payslips",
        }