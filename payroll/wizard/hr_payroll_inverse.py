# -- coding:utf-8 --
import logging
from odoo import _, fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class HrPayrollInverse(models.TransientModel):
    _name = "hr.payroll.inverse"

    def calculate_net_salary(self, _input):
        """Calculer le salaire net en fonction du sursalaire ou de la commission."""
        if not (payslip := self.env["hr.payslip"].browse(self._context.get("active_id"))):
            return

        total_ret = payslip.line_ids.filtered(lambda x: x.code == 'RET')
        categ_brut = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'IMPOSABLE' and x.code != 'COM' and x.code != 'EXCEPT' and x.code != 'CONG_PAY').mapped('amount'))
        wage = payslip.line_ids.filtered(lambda x: x.code == 'BASE')
        total_nimp = payslip.line_ids.filtered(lambda x: x.code == 'C_PNIMP')
        emp_input = payslip.line_ids.filtered(lambda x: x.code == 'EMP')

        # Log information
        _logger.info(f"############################ WORK100 {payslip.work_day}")
        _logger.info(f"############################ categ_brut {categ_brut}")
        _logger.info(f"############################ total_ret {total_ret.amount}")
        _logger.info(f"############################ wage {wage.amount}")
        _logger.info(f"############################ variable {_input}")
        _logger.info(f"############################ total_nimp {total_nimp.amount}")
        _logger.info(f"############################ emp_input {emp_input.amount}")

        if self.input_type == 'SURSA':
            # Existing logic for extra pay
            return ((wage.amount + _input + categ_brut) -
                (total_ret.amount) + total_nimp.amount) - emp_input.amount
        elif self.input_type == 'COM':
            return ((wage.amount + payslip.contract_id.extra_pay + payslip.special_bonus + _input + categ_brut) -
                (total_ret.amount) + total_nimp.amount) - emp_input.amount
        elif self.input_type == 'EXCEPT':
            return ((wage.amount + payslip.contract_id.extra_pay + payslip.bonus + _input + categ_brut) -
                    (total_ret.amount) + total_nimp.amount) - emp_input.amount
        return ((wage.amount + _input + categ_brut) -
                (total_ret.amount) + total_nimp.amount) - emp_input.amount

    def computeSlip(self):
        if not (payslip := self.env["hr.payslip"].browse(
                self._context.get("active_id"))):
            return

        if self.type_calcul == "net" and self.montant - payslip.contract_id.wage < 0:
            raise UserError(
                _(
                    f"Le salaire net saisi ({self.montant}) ne doit être inférieur au salaire de base ({payslip.contract_id.wage})"
                )
            )

        contract = payslip.contract_id
        if self.input_type == 'COM':
            payslip.bonus = 0  # Réinitialiser le bonus
            payslip.paid_leaves = 0  # Réinitialiser le montant des congés payés
        elif self.input_type == 'EXCEPT':
            payslip.special_bonus = 0  # Réinitialiser la prime exceptionnelle
            payslip.paid_leaves = 0  # Réinitialiser le montant des congés payés
        else:
            payslip.bonus = 0  # Réinitialiser le bonus
            payslip.special_bonus = 0 # Réinitialiser la prime exceptionnelle
            contract.extra_pay = 0  # Réinitialiser le sursalaire
            payslip.paid_leaves = 0 # Réinitialiser le montant des congés payés

        payslip.compute_sheet()
        if self.type_calcul == "net":
            if self.montant - contract.wage < 0:
                raise UserError(
                    _(
                        f"Le salaire net saisi ({self.montant}) ne doit être inférieur au salaire de base ({contract.wage})"
                    )
                )
            
            if contract.wage <= 0:
                raise UserError(
                    _(
                        f"Le salaire catégoriel doit être supérieur à 0."
                    )
                )

            target_net_salary = self.montant
            initial_input = payslip.contract_id.extra_pay
            if self.input_type == 'COM':
                initial_input = payslip.bonus
            elif self.input_type == 'EXCEPT':
                initial_input = payslip.special_bonus
            elif self.input_type == 'CONG':
                initial_input = payslip.paid_leaves

            tolerance = 0.1  # adjust as needed

            while abs(target_net_salary - payslip.net_wage) > tolerance:
                # Calculate net salary with current input
                calculated_net = self.calculate_net_salary(initial_input)

                # Variation check for avoiding an infinite loop
                if int(calculated_net) == int(target_net_salary):
                    break

                # Adjust input based on difference
                difference = target_net_salary - calculated_net
                adjustment = difference / 2  # adjust adjustment factor as needed
                initial_input += adjustment
                if self.input_type == 'SURSA':
                    payslip.contract_id.extra_pay = initial_input
                elif self.input_type == 'COM':
                    payslip.bonus = initial_input
                elif self.input_type == 'EXCEPT':
                    payslip.special_bonus = initial_input
                else:
                    payslip.paid_leaves = initial_input

                # Recalculate payslip with updated input
                payslip.compute_sheet()
                contract.total_net = target_net_salary

    type_calcul = fields.Selection(
        [('net', 'Par le net')], default='net', string='Méthode de calcul', required=True)
    input_type = fields.Selection(
        [
            ('SURSA', 'Sursalaire'), 
            ('COM', 'Commission'),
            ('EXCEPT', 'Prime exceptionnelle'),
            ('CONG', 'Congés'),
        ], default='SURSA', string='Variable à modifier', required=True)
    montant = fields.Integer("Montant")
