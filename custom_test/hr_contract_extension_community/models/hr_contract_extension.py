# -*- coding: utf-8 -*-

import time
from odoo import api, fields, osv, exceptions, models
from datetime import datetime
from odoo.tools.translate import _

from dateutil.relativedelta import relativedelta


class HrTypePiece(models.Model):
    _name = "hr.type.piece"
    _description = "Type de pièce d'identité"

    name = fields.Char("Désignation",required=True)
    description = fields.Text("Description")


class HrPieceIdentity(models.Model):
    _name = "hr.piece.identite"
    _rec_name = "numero_piece"
    _decription = "Pièce d'identité"

    numero_piece = fields.Char("Numéro de la pièce",required=True)
    nature_piece = fields.Selection([('attestion',"Attestation d'indentité"),("carte_sejour","Carte de séjour"),
                                   ("cni","CNI"),("passeport","Passeport")],string="Nature",required=True)
    date_etablissement = fields.Date("Date d'établissement",required=True)
    autorite=  fields.Char("Autorité",size=128)


class HrContract(models.Model):

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id
            self.department_id = self.employee_id.department_id
            self.date_start = self.employee_id.start_date


    def calcul_anciennete_actuel(self):
        anciennete = {}
        self.ensure_one()
        this_date = today = datetime.today()
        start_date = fields.Datetime.from_string(self.employee_id.start_date)
        if self.date_end:
            end_date = fields.Datetime.from_string(self.date_end)
            this_date = min(today, end_date)
        tmp = relativedelta(this_date, start_date) + relativedelta(months=+self.mois_report, years=+ self.an_report)
        print(tmp)
        anciennete = {
            'year_old': tmp.years,
            'month_old': tmp.months,
        }

        return anciennete


    def _get_anciennete(self):
        res = {}
        for ct in self:
            anciennete = ct.calcul_anciennete_actuel()
            if anciennete:
                ct.an_anciennete = anciennete['year_old']
                ct.mois_anciennete = anciennete['month_old']

    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    name = fields.Char('Nature du contrat', required=True)
    expatried = fields.Boolean('Expatrié', default=False)
    an_report = fields.Integer('Année')
    mois_report = fields.Integer('Mois report')
    an_anciennete = fields.Integer("Nombre d'année", compute='_get_anciennete')
    mois_anciennete = fields.Integer('Nombre de mois', compute='_get_anciennete')
    anne_anc = fields.Integer('Année')
    # sursalaire = fields.Integer('Sursalaire',required=False)
    hr_convention_id = fields.Many2one('hr.convention',"Convention",required=False)
    hr_secteur_id = fields.Many2one('hr.secteur.activite',"Secteur d'activité",required=False)
    categorie_salariale_id = fields.Many2one('hr.categorie.salariale', 'Catégorie salariale', required=False)
    # state= fields.Selection([('draft','Draft'),('in_progress',"En cours"),('ended','Terminé'),('cancel','Annulé')]
    #                         ,'Eat du contrat', select=True, readonly=True, default="draft")
    type_ended = fields.Selection([('licenced','Licencement'),('hard_licenced','Licencement faute grave'),
                ('ended','Fin de contract'),], 'Type de clôture')
    description_cloture = fields.Text("Motif de Clôture")
    # wage = fields.Integer('Salaire de base', required=True, related="categorie_salariale_id.salaire_base")

    def validate_contract(self):
        for ct in self:
            ct.write({'state':'open'})

    def closing_contract(self):
        view_id = self.env['ir.model.data'].get_object_reference('hr_contract_extension_community', 'hr_contract_closed_form_view')
        return {
                'name':_("Clôture de contrat"),
                'view_mode': 'form',
                'view_id': view_id[1],
                'view_type': 'form',
                'res_model': 'hr.contract.closed',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': self._context,
            }

    def action_cancel(self):
        for ct in self:
            ct.write({'state': 'cancel'})

    @api.onchange("hr_convention_id")
    def on_change_convention_id(self):
        if self.hr_convention_id:
            return {'domain': {'hr_secteur_id':[('hr_convention_id','=',self.hr_convention_id.id)]}}
        else :
            return {'domain': {'hr_secteur_id':[('hr_convention_id','=',False)]}}

    @api.onchange("hr_secteur_id")
    def on_change_secteur_id(self):
        if self.hr_secteur_id:
            return {'domain': {'categorie_salariale_id':[('hr_secteur_activite_id', '=', self.hr_secteur_id.id)]}}
        else :
            return {'domain': {'categorie_salariale_id':[('hr_secteur_activite_id', '=', False)]}}

    @api.onchange('categorie_salariale_id')
    def on_change_categorie_salariale_id(self):
        if self.categorie_salariale_id:
            self.wage = self.categorie_salariale_id.salaire_base

    def get_inputs_payslip(self):
        res = []
        if self.wage:
            type_line = self.env['hr.payslip.input.type'].search([('code', '=', 'WAGE')], limit=1)
            val = {
                'input_type_id': type_line.id,
                'amount': self.wage,
                'contract_id': self.id,
                #'struct_id': struct_id.id
            }
            res.append(val)
        return res


class HrCategorieSalarialePrime(models.Model):
    _name = "hr.categorie.salariale.prime"
    _description = "Gestion des primes de salaires catégoriels"

    prime_id = fields.Many2one("hr.payroll.prime", "Prime", required=True)
    amount = fields.Float("Montant", required=True)
    categorie_id = fields.Many2one("hr.contract.category", "Catégorie Salariale")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    cni_number = fields.Char("N° carte d'identité", required=False)


class HrConvention(models.Model):
    _name = "hr.convention"
    _description = "Convention"

    name = fields.Char("Name",required=True)
    description = fields.Text("Description")
    secteurs_ids = fields.One2many("hr.secteur.activite", "hr_convention_id", "Secteurs d'activtés")


class HrSecteurActivity(models.Model):
    _name = "hr.secteur.activite"
    _description = "Secteur d'activite"

    name = fields.Char("Nom",required=True)
    description = fields.Text("Description")
    hr_convention_id = fields.Many2one("hr.convention","Convention",required=True)
    salaire_ids = fields.One2many("hr.categorie.salariale","hr_secteur_activite_id","Catégories salariales")
    category_employee_ids = fields.One2many("hr.contract.category", "hr_secteur_activite_id", "Catégorie d'employés")


class HrContractCategory(models.Model):
    _inherit = "hr.contract.category"

    prime_ids = fields.One2many("hr.categorie.salariale.prime", 'categorie_id', "Primes")
    categorie_salariale_ids = fields.One2many("hr.categorie.salariale", "categorie_employee_id", "Salaires catégoriels")
    hr_secteur_activite_id = fields.Many2one('hr.secteur.activite', "Secteur d'activité", required=True)


# class HrCategorieSalarialePrime(models.Model):
#     _name = "hr.categorie.salariale.prime"
#     _description = "Gestion des primes de salaires catégoriels"
#
#     prime_id = fields.Many2one("hr.payroll.prime", "Prime", required=True)
#     amount = fields.Float("Montant", required=True)
#     categorie_id = fields.Many2one("hr.categorie.salariale", "Catégorie Salariale")


class HrCategorieSalariale(models.Model):
    _name = "hr.categorie.salariale"
    _description = "Categorie salariale"

    name = fields.Char('Libellé', required=False)
    salaire_base = fields.Integer("Salaire de base")
    description = fields.Text('Description')
    hr_secteur_activite_id = fields.Many2one('hr.secteur.activite', "Secteur d'activité")
    categorie_employee_id = fields.Many2one("hr.contract.category", "Catégorie de l'employé")
