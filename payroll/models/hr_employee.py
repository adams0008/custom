import logging
from collections import defaultdict
from datetime import datetime

import odoo.addons.decimal_precision as dp
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    slip_ids = fields.One2many(
        "hr.payslip", "employee_id", string="Payslips", readonly=True
    )
    payslip_count = fields.Integer(
        groups="payroll.group_payroll_user",
    )

    def getWorkedDays(self, date_from, date_to, contract):
        return {
            "name": _("Normal Working Days paid at 100%"),
            "sequence": 1,
            "code": "WORK100",
            "number_of_days": 30,
            "number_of_hours": 173.33,
            "contract_id": contract.id,
        }

    def _get_part_igr(self):
        result = 0
        for rec in self:
            if rec.marital:
                t1 = rec.marital
                B38 = t1[0]
                B39 = rec.children
                # B40 = rec.enfants_a_charge

                if B38 in ["s", "d"]:
                    if B39 == 0:
                        result = 1
                    else:
                        result = 5 if B39 * 0.5 > 5 - 1.5 else 1.5 + B39 * 0.5
                elif B38 == "m" and B39 == 0:
                    result = 2
                elif B38 == "m" or B38 == "w" and B39 != 0:
                    result = 5 if B39 > 6 else 2 + 0.5 * B39
                elif B38 == "w":
                    result = 1
                else:
                    result += 2 + 0.5 * B39
            rec.part_igr = result

    # nouveau champ
    service = fields.Char("Service")
    indice = fields.Char("Indice")
    coeff = fields.Char("Coefficient")
    niveau = fields.Char("Niveau")
    cnps = fields.Char("N° CNPS", size=64)
    date_first_contract = fields.Date(
        string="Date embauche 1er contract", compute="first_contract", required=False
    )
    payment_method_id = fields.Many2one(
        "payment.method.employee", string="Moyens de paiement", required=False
    )
    category_employee_id = fields.Many2one(
        comodel_name="hr.category.employee", string="Categorie employé", required=False
    )
    part_igr = fields.Float(compute=_get_part_igr, string="Part IGR")
    cmu_employee = fields.Integer(
        compute="_compute_cmu_amount",
        string="CMU employé",
        digits_compute=dp.get_precision("Account"),
    )
    cmu_employeur = fields.Integer(
        string="CMU employeur",
        compute="_compute_cmu_amount",
        digits_compute=dp.get_precision("Account"),
    )
    date_retour_conge = fields.Date(string="Date de rétour congé")
    date_depart_conge = fields.Date(string="Date de départ congé")
    indemnite_licencement = fields.Integer(
        store=True,
        readonly=True,
        string="Indemnite licencement",
        compute="_get_indemnite_licencement",
        digits_compute=dp.get_precision("Account"),
    )
    indemnite_licencement2 = fields.Integer(
        digits_compute=dp.get_precision("Account"), string="Indemnite licencement2"
    )
    
    indemnite_fin_cdd = fields.Integer(
        string="Indemnité fin CDD",
        store=True,
        readonly=True,
        compute="_get_indemnite_fin_cdd",
        digits_compute=dp.get_precision("Account"),
    )
    indemnite_retraite = fields.Integer(
        string="Indemnite retraite",
        store=True,
        readonly=True,
        compute="_get_indemnite_licencement",
    )
    indemnite_retraite2 = fields.Integer(
        digits_compute=dp.get_precision("Account"), string="Indemnite retraite"
    )
    indemnite_deces = fields.Integer(
        string="Indemnite décès",
        store=True,
        readonly=True,
        compute="_get_indemnite_deces",
    )
    indemnite_deces2 = fields.Integer(
        digits_compute=dp.get_precision("Account"), string="Indemnite décès"
    )
    indemnite_months = fields.Integer(string="Nbre de mois de preavis", default=1)
    indemnite_preavis = fields.Integer(
        store=True,
        string="Indemnite préavis",
        compute="_get_indemnite_preavis",
        digits_compute=dp.get_precision("Account"),
    )
    conge_paye = fields.Boolean("Congé payé")
    debut_rupture = fields.Date("Date rupture")
    debut_decompte = fields.Date("Début décompte")
    is_retraite = fields.Boolean("Retraité")
    is_deces = fields.Boolean("Décès")
    notification_date = fields.Date(compute="_get_end_contract")
    contract_id = fields.Many2one("hr.contract")
    contracts = fields.Many2one(
        "hr.contract",
        default=lambda self: self.env["hr.contract"].search(
            [("employee_id", "=", self.id)]
        ),
    )
    date_end = fields.Date(
        related="contract_id.date_end",
        store=True,
        domain=[("contract_type_id.code", "=", "CDD")],
    )
    taken_days_number_year = fields.Integer(
        string="Nombre de jour(s) pris par an")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.user.company_id
    )
    count_employee_slip = fields.Integer(
        string="Count_employee_slip",
        required=False,
        compute="_get_employee_slip_number",
    )
    prime_gratification = fields.Integer(
        string="Gratification",
        store=True,
        readonly=True,
        compute="_compute_prime_gratification",
        digits_compute=dp.get_precision("Account"),
    )

    def button_employee_payslip(self):
        """
        Redirige l'utilisateur vers les fiches de paie de l'employé
        """
        return {
            "name": "Bulletin de paie",
            "res_model": "hr.payslip",
            "view_mode": "tree,form",
            # 'context': {'search_default_employee_id': self.id},
            "domain": [("employee_id", "=", self.id)],
            "target": "current",
            "type": "ir.actions.act_window",
        }
    
    @api.constrains('indemnite_months')
    def get_current_indemnite_month_value(self):
        for record in self:
            if isinstance(record.indemnite_months, int) and not (1 <= record.indemnite_months <= 4):
                raise ValidationError("Le nombre de mois de préavis doit être compris entre 1 et 4.")

    @api.depends("slip_ids")
    def _get_employee_slip_number(self):
        for rec in self:
            rec.count_employee_slip = rec.env["hr.payslip"].search_count(
                [("employee_id", "=", rec.id)]
            )

    def main_function(self):
        _logger.info("Fonction principale pour le calcul des paramètres")
        for emp in self:
            emp.compute_all_function(emp)

    def compute_all_function(self, emp):
        _logger.info("Fonction après chaque employé")
        emp._get_indemnite_licencement()
        emp._get_indemnite_fin_cdd()
        emp._get_indemnite_deces()
        emp._get_end_contract()
        emp._compute_cmu_amount()
        emp._compute_prime_gratification()
        # emp._get_reference_period()
        emp._get_indemnite_preavis()

    def _compute_cmu_amount(self):
        for rec in self:
            if rec:
                cmu_id = self.env["hr.config"].search([], limit=1)
                amount = cmu_id and cmu_id.cmu or 0
                cmu_children = amount * rec.children
                cmu_emp = rec.marital == "married" and amount * 2 or amount
                cmu = (cmu_emp + cmu_children) / 2
                rec.cmu_employee = rec.cmu_employeur = cmu

    @api.depends("contract_id")
    def first_contract(self):
        for record in self:
            record.date_first_contract = False
            if res := self.env["hr.contract"].search(
                [("employee_id", "=", record.id)], order="id asc", limit=1
            ):
                record.date_first_contract = res.date_start

    def diff_month(self, d1, d2):
        return (d1.year - d2.year) * 12 + d1.month - d2.month

    def _compute_prime_gratification(self):
        for rec in self:
            payslips = (
                rec.env["hr.payslip"]
                .search(
                    [
                        ("employee_id", "=", rec.id),
                        ("gratification", "=", True),
                        ("contract_id", "=", rec.contract_id.id),
                    ],
                    order="date_to desc",
                    limit=2,
                )
                .mapped("date_to")
            )
            seniority_in_months = 0
            if len(payslips) >= 2 and rec.contract_id.date_start:
                seniority_in_months = rec.diff_month(payslips[0], payslips[1])
            elif rec.contract_id.date_start and payslips:
                seniority_in_months = rec.diff_month(
                    payslips[0], rec.contract_id.date_start
                )
            else:
                rec.prime_gratification = 0
        if seniority_in_months != 0:
            rec.prime_gratification = (
                rec.contract_id.wage * seniority_in_months * 0.75
            ) / 12

    def _get_end_contract(self):
        self.ensure_one()
        for emp in self:
            date_end = (
                emp.env["hr.contract"]
                .search(
                    [
                        ("employee_id", "=", emp.id),
                        ("contract_type_id.code", "=", "CDD"),
                    ]
                )
                .date_end
            )
            emp.notification_date = date_end if date_end is not False else False

    def _get_indemnite_licencement(self):
        for emp in self:
            emp_id = emp.ids[0]
            slip_obj = emp.env["hr.payslip"].search([])
            employee = emp.env["hr.employee"].search([("id", "=", emp_id)])
            if emp.debut_decompte and emp.debut_rupture and not emp.is_retraite:
                payslips = slip_obj.search(
                    [
                        ("employee_id", "=", emp.id),
                        ("date_from", ">=", emp.debut_decompte),
                        ("date_from", "<=", emp.debut_rupture),
                    ]
                )
                payslips_number = len(payslips)
                montant_net = 0.0
                montant_avt = 0
                for slip in payslips:
                    line_ids = slip.line_ids
                    input_line_ids = emp.env["hr.payslip.input"].search(
                        [("payslip_id", "=", slip.id)]
                    )
                    montant = sum(
                        line.total for line in line_ids if line.code == "BRUT"
                    )

                    montant_net += montant

                SNMM = montant_net / payslips_number if payslips_number else 0
                _logger.info("_get_indemnite_licencement %s", SNMM)
                if emp.contract_id.an_anciennete:
                    year = emp.contract_id.an_anciennete
                    if 0 <= year <= 6:
                        amount = (SNMM * 30) / 100
                        emp.indemnite_licencement = amount
                        indemnite_licencement2 = (SNMM * 30) / 100
                        employee.write(
                            {"indemnite_licencement2": indemnite_licencement2}
                        )
                        employee.write({"indemnite_retraite2": 0.0})
                    elif 6 <= year <= 10:
                        emp.indemnite_licencement = ((SNMM * 30) / 100) + (
                            (SNMM * 35) / 100
                        )
                        indemnite_licencement2 = ((SNMM * 30) / 100) + (
                            (SNMM * 35) / 100
                        )
                        employee.write(
                            {"indemnite_licencement2": indemnite_licencement2}
                        )
                        employee.write({"indemnite_retraite2": 0.0})
                    elif year > 10:
                        # emp.indemnite_licencement = 0
                        emp.indemnite_licencement = (
                            ((SNMM * 30) / 100)
                            + ((SNMM * 35) / 100)
                            + ((SNMM * 40) / 100)
                        )
                        indemnite_licencement2 = (
                            ((SNMM * 30) / 100)
                            + ((SNMM * 35) / 100)
                            + ((SNMM * 40) / 100)
                        )
                        employee.write(
                            {"indemnite_licencement2": indemnite_licencement2}
                        )
                        employee.write({"indemnite_retraite2": 0.0})
            if emp.debut_decompte and emp.debut_rupture and emp.is_retraite:
                payslips = slip_obj.search(
                    [
                        ("employee_id", "=", emp.id),
                        ("date_from", ">=", emp.debut_decompte),
                        ("date_from", "<=", emp.debut_rupture),
                    ]
                )
                payslips_number = len(payslips)
                montant_net = 0
                montant_avt = 0
                for slip in payslips:
                    line_ids = slip.line_ids
                    input_line_ids = emp.env["hr.payslip.input"].search(
                        [("payslip_id", "=", slip.id)]
                    )
                    montant = sum(
                        line.total for line in line_ids if line.code == "BASE_IMP"
                    )
                    montant_net += montant
                SNMM = montant_net / payslips_number if payslips_number else 0
                _logger.info("_get_indemnite_licencement %s", SNMM)
                if emp.contract_id.an_anciennete:
                    year = emp.contract_id.an_anciennete
                    if 0 <= year <= 6:
                        emp.indemnite_retraite = (SNMM * 30) / 100
                        indemnite_retraite2 = (SNMM * 30) / 100
                        employee.write(
                            {"indemnite_retraite2": indemnite_retraite2})
                        employee.write({"indemnite_licencement2": 0.0})
                    elif 6 <= year <= 10:
                        emp.indemnite_retraite = ((SNMM * 30) / 100) + (
                            (SNMM * 35) / 100
                        )
                        indemnite_retraite2 = (
                            (SNMM * 30) / 100) + ((SNMM * 35) / 100)
                        employee.write(
                            {"indemnite_retraite2": indemnite_retraite2})
                        employee.write({"indemnite_licencement2": 0.0})
                    elif year > 10:
                        emp.indemnite_retraite = (
                            ((SNMM * 30) / 100)
                            + ((SNMM * 35) / 100)
                            + ((SNMM * 40) / 100)
                        )
                        indemnite_retraite2 = (
                            ((SNMM * 30) / 100)
                            + ((SNMM * 35) / 100)
                            + ((SNMM * 40) / 100)
                        )
                        employee.write(
                            {"indemnite_retraite2": indemnite_retraite2})
                        employee.write({"indemnite_licencement2": 0.0})
            if not emp.debut_decompte and not emp.debut_rupture and not emp.is_retraite:
                emp.indemnite_licencement = 0
                emp.indemnite_retraite = 0

    def _get_indemnite_fin_cdd(self):
        montant = 0
        for emp in self:
            emp_id = emp.ids[0]
            if emp.contract_id.date_start:
                payslip = emp.env["hr.payslip"].search(
                    [("employee_id", "=", emp.id)])
                if payslip != 0:
                    for slip in payslip:
                        for line in slip.line_ids:
                            if line.code == "BRUT":
                                montant += line.total
                    if montant:
                        emp.indemnite_fin_cdd = round(montant * 0.03)
                        _logger.info(
                            "Indemnité fin cdd %s",
                            emp.indemnite_fin_cdd)
            else:
                emp.indemnite_fin_cdd = 0

    def _get_indemnite_deces(self):
        for emp in self:
            emp_id = emp.ids[0]
            employee = emp.env["hr.employee"].search([("id", "=", emp_id)])
            _logger.info("Indemnité de décès de l'employe %s", employee)
            if emp.contract_id.an_anciennete and emp.is_deces:
                year = emp.contract_id.an_anciennete
                wage = emp.contract_id.wage
                if 0 <= year <= 6:
                    emp.indemnite_deces = wage * 3
                    indemnite_deces2 = wage * 3
                    employee.write({"indemnite_deces2": indemnite_deces2})
                elif 6 <= year <= 10:
                    emp.indemnite_deces = (wage * 4) + (wage * 3)
                    indemnite_deces2 = (wage * 4) + (wage * 3)
                    employee.write({"indemnite_deces2": indemnite_deces2})
                elif year > 10:
                    emp.indemnite_deces = (wage * 6) + (wage * 4) + (wage * 3)
                    indemnite_deces2 = (wage * 6) + (wage * 4) + (wage * 3)
                    employee.write({"indemnite_deces2": indemnite_deces2})
            if emp.contract_id.an_anciennete and not emp.is_deces:
                emp.indemnite_deces = 0
            if not emp.contract_id.an_anciennete and not emp.is_deces:
                emp.indemnite_deces = 0
            if not emp.contract_id.an_anciennete and emp.is_deces:
                emp.indemnite_deces = 0

    def _get_indemnite_preavis(self):
        for emp in self:
            emp_id = emp.ids[0]
            slip_obj = emp.env["hr.payslip"].search([])
            employee = emp.env["hr.employee"].search([("id", "=", emp_id)])
            _logger.info("Indemnité de preavis de l'employe %s", employee)
            payslips = slip_obj.search(
                [
                    ("employee_id", "=", emp.id),
                ], limit=1
            )
            salaire = 0
            transport = 0
            for slip in payslips:
                line_ids = slip.line_ids
                emp.env["hr.payslip.input"].search(
                    [("payslip_id", "=", slip.id)], limit=1
                )
                salaire = sum(
                    line.total for line in line_ids if line.code == "BRUT"
                )
                transport = sum(
                    line.total for line in line_ids if line.code == "TRSP"
                )

            if emp.indemnite_months:
                emp.indemnite_preavis = emp.indemnite_months * salaire
            else:
                if emp.contract_id.an_anciennete:
                    year = emp.contract_id.an_anciennete
                    dure_preavis = 0
                    if 0 <= year <= 6:
                        dure_preavis = 1
                    elif 6 <= year <= 11:
                        dure_preavis = 2
                    elif 11 <= year <= 16:
                        dure_preavis = 3
                    elif year > 16:
                        dure_preavis = 4
                    emp.indemnite_preavis = dure_preavis * salaire
                else:
                    emp.indemnite_preavis = salaire
