import logging
from collections import defaultdict
from datetime import datetime, date

import odoo.addons.decimal_precision as dp
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """

    _inherit = "hr.contract"
    _description = "Employee Contract"

    struct_id = fields.Many2one("hr.payroll.structure", string="Salary Structure")
    schedule_pay = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi-annually", "Semi-annually"),
            ("annually", "Annually"),
            ("weekly", "Weekly"),
            ("bi-weekly", "Bi-weekly"),
            ("bi-monthly", "Bi-monthly"),
        ],
        string="Scheduled Pay",
        index=True,
        default="monthly",
        help="Defines the frequency of the wage payment.",
    )
    resource_calendar_id = fields.Many2one(
        required=True, help="Employee's working schedule."
    )

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
                 hierachy (parent=False first, then first level children and
                 so on) and without duplicates
        """
        structures = self.mapped("struct_id")
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    payment_method_id = fields.Many2one(
        "payment.method.employee", string="Moyens de paiement", required=False
    )
    category_salary_id = fields.Many2one(
        "category.salary", string="Catégorie Salariale", required=False
    )
    # sector_activity_id = fields.Many2one(
    #     "sector.activities",
    #     string="Secteur d'activité",
    #     related="category_salary_id.sector_activity_id",
    #     required=False,
    # )
    extra_pay = fields.Float(string="Sursalaire", default=0, required=True)
    seniority = fields.Char(
        string="Ancienneté", required=False
    )

    # primes_not_imposable_ids = fields.One2many(
    #     comodel_name="hr.contract.prime",
    #     inverse_name="contract_id",
    #     string="Primes et avantages",
    #     required=False,
    # )

    primes_ids = fields.One2many(
        comodel_name="hr.contract.prime",
        inverse_name="contract_id",
        string="Primes et avantages",
        required=False,
    )
    # # i add a new field here
    struct_id = fields.Many2one(
        "hr.payroll.structure",
        string="Structure Salariale")
    an_anciennete = fields.Integer(
        "Nombre d'année",
        compute="_get_anciennetes")
    mois_anciennete = fields.Integer(
        "Nombre de mois", compute="_get_anciennetes")
    total_net = fields.Monetary(string="Net à Payer sur un mois")
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))

    @api.model
    def _create_dynamic_sequence(self):
        # Créer une séquence dynamique avec un code spécifique à hr.contract
        sequence = self.env['ir.sequence'].search([('code', '=', 'hr.contract')], limit=1)
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': 'HR Contract Sequence',
                'code': 'hr.contract',
                'padding': 3,
                'implementation': 'no_gap',
            })
        return sequence

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            sequence = self._create_dynamic_sequence()
            current_year = datetime.now().year
            sequence_number = sequence.next_by_id() or '000'
            vals['name'] = f"DRH/{current_year}/{sequence_number}"
        return super(HrContract, self).create(vals)
    

    def _get_work_hours(self, date_from, date_to, domain=None):
        """
        Returns the amount (expressed in hours) of work
        for a contract between two dates.
        If called on multiple contracts, sum work amounts of each contract.
        :param date_from: The start date
        :param date_to: The end date
        :returns: a dictionary {work_entry_id: hours_1, work_entry_2: hours_2}
        """

        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())
        work_data = defaultdict(int)

        # First, found work entry that didn't exceed interval.
        # work_entries = self.env['hr.work.entry']._read_group(
        #     self._get_work_hours_domain(date_from, date_to, domain=domain, inside=True),
        #     ['hours:sum(duration)'],
        #     ['work_entry_type_id']
        # )
        # j'ai remplacé le champ
        work_entries = self.env["hr.work.entry"].read_group(
            self._get_work_hours_domain(
                date_from, date_to, domain=domain, inside=True),
            fields=["work_entry_type_id", "hours:sum(duration)"],
            groupby=["work_entry_type_id"],
        )

        work_data |= {
            (
                data["work_entry_type_id"][0]
                if data["work_entry_type_id"]
                else False
            ): data["hours"]
            for data in work_entries
        }
        self._preprocess_work_hours_data(work_data, date_from, date_to)

        # Second, find work entry that exceeds interval and compute right
        # duration.
        work_entries = self.env["hr.work.entry"].search(
            self._get_work_hours_domain(
                date_from, date_to, domain=domain, inside=False)
        )

        for work_entry in work_entries:
            date_start = max(date_from, work_entry.date_start)
            date_stop = min(date_to, work_entry.date_stop)
            if work_entry.work_entry_type_id.is_leave:
                contract = work_entry.contract_id
                calendar = contract.resource_calendar_id
                employee = contract.employee_id
                contract_data = employee._get_work_days_data_batch(
                    date_start, date_stop, compute_leaves=False, calendar=calendar
                )[employee.id]

                work_data[work_entry.work_entry_type_id.id] += contract_data.get(
                    "hours", 0
                )
            else:
                work_data[
                    work_entry.work_entry_type_id.id
                ] += work_entry._get_work_duration(
                    date_start, date_stop
                )  # Number of hours
        return work_data

    def annees_et_mois_ecoules(self, date_debut):
        if date_debut:
            aujourdhui = datetime.now()
            annees = aujourdhui.year - date_debut.year
            mois = aujourdhui.month - date_debut.month
            if mois < 0:
                annees -= 1
                mois += 12
            return {"annees": annees, "mois": mois}
        

    # @api.depends("date_start")
    # def _get_anciennete(self):
    #     for rec in self:
    #         rec.seniority = "0 An(s) - 0 mois"
    #         if rec.date_start:
    #             today = datetime.now()
    #             year = today.year - rec.date_start.year
    #             month = today.month - rec.date_start.month
    #             if month < 0:
    #                 year -= 1
    #                 month += 12
    #             rec.seniority = f"{str(year)} An(s) - {str(month)} mois"

    @api.depends("date_start")
    def _get_dict_anciennete(self):
        for rec in self:
            if rec.date_start:
                today = datetime.now()
                year = today.year - rec.date_start.year
                month = today.month - rec.date_start.month
                if month < 0:
                    year -= 1
                    month += 12
                return {"year": year, "month": month}

    @api.depends("date_start")
    def _get_anciennetes(self):
        res = {}
        # anciennete = self.calcul_anciennete_actuel()
        for rec in self:
            if anciennete := self.annees_et_mois_ecoules(rec.date_start):
                rec.an_anciennete = anciennete.get("annees")
                rec.mois_anciennete = anciennete.get("mois")
            else:
                rec.an_anciennete = 0
                rec.mois_anciennete = 0


    @api.onchange("primes_ids.prime_id")
    def _compute_amount_prime(self):
        for rec in self:
            for prime_contract in rec.primes_ids:
                primes = rec.env["hr.payroll.prime"].search(
                    [("id", "=", prime_contract.prime_id.id)]
                )
                for prime in primes:
                    prime_contract.amount = prime.amount_prime


class hr_contract_prime(models.Model):
    _name = "hr.contract.prime"
    _description = "Prime"

    contract_id = fields.Many2one(
        comodel_name="hr.contract", string="Contrat", required=True
    )
    not_imposable_id = fields.Many2one(
        comodel_name="hr.payroll.prime",
        string="Prime Non imposable",
        required=False,
    )

    prime_id = fields.Many2one(
        comodel_name="hr.payroll.prime",
        string="Primes",
        required=False,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id,
    )

    amount_not_imp = fields.Monetary(string="Montant")
    amount_imp = fields.Monetary(string="Montant")

    amount_prime = fields.Monetary(string="Montant", readonly=False)
    type = fields.Selection(
        string="Type",
        selection=[("imposable", "Imposable"),
                   ("not_imposable", "Non imposable")],
        required=False,
    )

    # @api.onchange('prime_id')
    # def _onchange_not_imposable_id(self):
    #     if self.prime_id:
    #         self.amount_prime = self.prime_id.amount