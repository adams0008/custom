# -*- coding: utf-8 -*-

import time
from collections import defaultdict
from datetime import datetime

from odoo import api, fields, models


class SectorActivities(models.Model):
    _name = "sector.activities"
    _description = "Secteur d'activité"

    name = fields.Char("Secteur d'activité")


class CategoryEmployee(models.Model):
    _name = "hr.category.employee"
    _description = "Categorie Employé"

    name = fields.Char("Categorie Employé")


class PaymentMethodEmployee(models.Model):
    _name = "payment.method.employee"
    _description = "Moyens de paiement salaire"

    name = fields.Char("Moyens de paiement")


class HrPayrollPrime(models.Model):
    _name = "hr.payroll.prime"
    _description = "Prime"

    name = fields.Char("Prime", size=64, required=True)
    code = fields.Char("Code", size=64, required=True)
    description = fields.Text("Description")
    type = fields.Selection(
        string="Type",
        selection=[("imposable", "Imposable"),
                   ("not_imposable", "Non imposable")],
        required=False,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(string="Montant")


class CategoryEmployee(models.Model):
    _name = "category.salary"
    _description = "Categorie Salariale"

    name = fields.Char("Categorie salariale", required=True)
    sector_activity_id = fields.Many2one(
        "sector.activities", string="Secteur d'activité", required=False
    )
    base = fields.Float(string="Salaire de Base", required=True)


class Company(models.Model):
    _inherit = "res.company"

    cnps = fields.Char(string="N°Cnps", required=False)


class hr_config(models.Model):
    _name = "hr.config"
    _description = "Configurations salariales "

    name = fields.Char("Code fiche de paie", size=128)
    cmu = fields.Float("Couverture Maladie Universelle (CMU)", digits=(6, 2))
    holiday = fields.Float("Coefficient jours de conges acquis", digits=(6, 2))
    days_work = fields.Float("Jour Travaillé")
