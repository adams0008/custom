# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
import logging
_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    reconcile_mode = fields.Selection(
        [("edit", "Edit Move"), ("keep", "Keep Suspense Accounts")],
        default="edit",
        required=True,
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", string="Company Currency"
    )
    reconcile_aggregate = fields.Selection(
        [
            ("statement", "Statement"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
        ],
        string="Reconcile aggregation",
        help="Aggregation to use on reconcile view",
    )

    def get_rainbowman_message(self):
        self.ensure_one()
        if (
            self._get_journal_dashboard_data_batched()[self.id]["number_to_reconcile"]
            > 0
        ):
            return False
        return _("Well done! Everything has been reconciled")
    
    def _get_journal_dashboard_data_batched(self):
        data = super(AccountJournal, self)._get_journal_dashboard_data_batched()
        _logger.info(f"data _get_journal_dashboard_data_batched {data}")
        return data

    def open_action(self):
        self.ensure_one()
        if self.type not in ["bank", "cash"]:
            return super().open_action()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account_reconcile_oca.action_bank_statement_line_reconcile_all"
        )
        return action
