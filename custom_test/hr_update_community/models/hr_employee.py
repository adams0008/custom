# -*- encoding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2012 Veone - support.veone.net
# Author: Veone
#
# Fichier du module hr_emprunt
# ##############################################################################  -->
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo import fields, models, api, _


#Type_employee = [('h', 'Horaire'), ('j', 'Journalier'), ('m', 'Mensuel')]


class hr_employee_degree(models.Model):
    _name = "hr.employee.degree"
    _description = "Degree of employee"

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of degrees.", default=1)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the Degree of employee must be unique!')
    ]


class licence(models.Model):
    _name = "hr.licence"
    _description = "Licence employé"

    name = fields.Char('Libellé Licence', required=True, readonly=False)
    reference = fields.Char('Reférence', required=False, readonly=False)
    date_debut = fields.Date('Début validité')
    date_fin = fields.Date('Fin validité')
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False)


class domaine(models.Model):
    _name = "hr.diplomes.domaine"
    _description = "Domaine de diplome employe"
    _rec_name = 'libelle'

    libelle = fields.Char('Libellé Domaine', required=True, readonly=False)


class DiplomeEmploye(models.Model):
    _name = "hr.diplomes.employee"
    _description = "Diplome employe"

    name = fields.Char('Nom')
    diplome_id = fields.Many2one('hr.employee.degree', 'Niveau', required=True)
    domaine_id = fields.Many2one('hr.diplomes.domaine', 'Domaines', required=False, readonly=False)
    reference = fields.Char('Reférence', required=False, readonly=False)
    date_obtention = fields.Date("Date d'obtention")
    date_start = fields.Date("Date début")
    date_end = fields.Date("Date fin")
    type = fields.Selection([
        ('diplome', 'Diplôme'),
        ('certif', 'Certification')], string="Type")
    image = fields.Binary('Image')
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False)


class visa(models.Model):
    _name = "hr.visa"
    _description = "visa employé"

    name = fields.Char('Libellé visa', required=True, readonly=False)
    reference = fields.Char('N° Visa', required=True, readonly=False)
    pays_id = fields.Many2one('res.country', 'Pays', required=True)
    date_debut = fields.Datetime('Début validité')
    date_fin = fields.Datetime('Fin validité')
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False)


class carte_sejour(models.Model):
    _name = "hr.carte.sejour"
    _description = "Carte de séjour employé"

    name = fields.Char('Libellé visa', required=False, readonly=False)
    reference = fields.Char('N° Visa', required=False, readonly=False)
    pays_id = fields.Many2one('res.country', 'Pays', required=False)
    date_debut = fields.Datetime('Début validité')
    date_fin = fields.Datetime('Fin validité')
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False)


class enfants_employe(models.Model):
    _name = "hr.employee.enfant"
    _description = "Enfants de l'employé"

    @api.depends('date_naissance')
    def _get_age_child(self):
        this_date = fields.Datetime.now()
        for child in self:
            date_naissance = fields.Datetime.from_string(child.date_naissance)
            tmp = relativedelta(this_date, date_naissance)
            child.age = tmp.years

    name = fields.Char('Nom', required=True, readonly=False)
    date_naissance = fields.Date("Date de naissance", required=True)
    mobile = fields.Char('Portable', required=False, readonly=False)
    email = fields.Char('email', required=False, readonly=False)
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False)
    age = fields.Integer('Âge', compute="_get_age_child")
    link = fields.Selection([
        ('enfant', 'Enfant'),
        ('frere', "Frère"),
        ('soeur', 'Soeur'),
        ('cousin', 'Cousin'),
        ('cousine', 'Cousine'),
        ('other', 'Autres')], 'Lien de parenté', readonly=False)


class HrParentEmployee(models.Model):
    _name = "hr.parent.employe"
    _description = "les parents de l'employee"

    name = fields.Char('Nom', required=True, readonly=False)
    date_naissance = fields.Date("Date de naissance")
    mobile = fields.Char('Portable', required=False, readonly=False)
    email = fields.Char('email', required=False, readonly=False)
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False)
    link = fields.Selection([
        ('pere', "Père"),
        ('mere', "Mère"),
    ], 'Lien de parenté', readonly=False)


class HrPersonneContact(models.Model):
    _name = 'hr.personne.contacted'
    _description = 'Personnes a contacter'

    name = fields.Char("Name", required=True)
    email = fields.Char("Email")
    portable = fields.Char('Portable', required=True)
    state = fields.Selection([('grand_parent', 'Grand père/Grande mère'),('parent', 'Père / Mère'),
              ('conjoint', 'Conjoint(e)'), ('enfant', 'Enfant'), ('frere', 'Frère / Soeur'), ('voisin', 'Voisin'),
              ('oncle', 'Oncle/Tante'), ('cousin', 'Cousin / Cousine'), ('other', 'Autres')], 'Type de lien', readonly=False)
    Lien = fields.Char("Le lien")
    employee_id = fields.Many2one("hr.employee", 'Employé')

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    @api.depends("marital","children", "enfants_a_charge")
    @api.onchange("marital","children", "enfants_a_charge")
    def _get_part_igr(self):
        # La nouvelle methode de calcul de la part IGR
        for rec in self:
            if rec.marital in ('single', 'divorced', 'widower'):
                if rec.enfants_a_charge == 0:
                    nb_parts = 1
                elif rec.enfants_a_charge == 1:
                    nb_parts = 2 
                elif rec.enfants_a_charge == 2:
                    nb_parts = 2.5 
                elif rec.enfants_a_charge == 3:
                    nb_parts = 3
                else:
                    nb_parts = 3.5 + (rec.enfants_a_charge - 4) * 0.5
                
                if rec.marital == 'widower' and rec.enfants_a_charge>0 :
                    nb_parts += 0.5 

            elif rec.marital == 'married':
                if rec.enfants_a_charge == 0:
                    nb_parts = 2
                elif rec.enfants_a_charge == 1:
                    nb_parts = 2.5
                elif rec.enfants_a_charge == 2:
                    nb_parts = 3
                elif rec.enfants_a_charge == 3:
                    nb_parts = 3.5
                else:
                    nb_parts = 4 + (rec.enfants_a_charge - 4) * 0.5
            else:
                raise UserError(_("Statut matrimonial invalide. Les valeurs acceptées sont 'celibataire', 'marie', 'divorce' et 'veuf'."))
            
            nb_parts = 5 if nb_parts >= 5 else nb_parts
            
            rec.part_igr=nb_parts
        


    def _compute_children(self):
        for emp in self:
            print(emp.enfants_ids)
            emp_id = emp.ids[0]
            print(emp_id)
            employee = emp.env['hr.employee'].search([('id', '=', emp_id)])
            if emp:
                number_cmu = 1
                enfants_ids = employee.enfants_ids
                if len(enfants_ids) != 0:
                    for enfant in enfants_ids:
                        date_ref = datetime.now().strftime('%Y-%m-%d')
                        date_naiss = enfant.date_naissance
                        temp1 = datetime.strptime(date_ref, '%Y-%m-%d')
                        temp2 = datetime.strptime(str(date_naiss), '%Y-%m-%d')
                        age = abs(relativedelta(temp2, temp1).years)
                        if 0 < age <= 21:
                            number_cmu += 1
                    cmu = 1000 * number_cmu
                    cmu_employe2 = (cmu * 50) / 100
                    cmu_employeur2 = (cmu * 50) / 100
                    emp.cmu_employe = cmu_employe2
                    emp.cmu_employeur = cmu_employeur2
                    employee.write({'cmu_employe2': cmu_employe2})
                    employee.write({'cmu_employeur2': cmu_employeur2})
                else:
                    cmu = 1000 * number_cmu
                    cmu_employe2 = (cmu * 50) / 100
                    cmu_employeur2 = (cmu * 50) / 100
                    emp.cmu_employe = cmu_employe2
                    emp.cmu_employeur = cmu_employeur2
                    employee.write({'cmu_employe2': cmu_employe2})
                    employee.write({'cmu_employeur2': cmu_employeur2})
            else:
                emp.cmu_employe = 0
            total_children = 0
            if emp.enfants_ids:
                total_children = len(emp.enfants_ids)
            children_in_charge = 0
            for child in emp.enfants_ids:
                if child.age <= emp.company_id.max_age_child:
                    children_in_charge += 1
            # emp.children = children_in_charge
            emp.total_children = total_children

    @api.depends('birthday')
    def _get_age_employee(self):
        this_date = fields.Datetime.now()
        for emp in self:
            emp.age = emp._get_age(this_date)

    @api.depends('start_date', 'end_date')
    def _get_seniority(self):
        today = fields.Datetime.now()
        for emp in self:
            start_date = fields.Datetime.from_string(emp.start_date)
            print("La date de fin est %s" % emp.end_date)
            if emp.end_date:
                end_date = fields.Datetime.from_string(emp.end_date)
                this_date = min(today, end_date)
            else:
                this_date = today
            tmp = relativedelta(this_date, start_date)
            emp.seniority_employee = tmp.years

    def name_get(self):
        result = []
        for emp in self:
            if emp.first_name:
                name = emp.name + ' ' + emp.first_name
            else:
                name = emp.name
            result.append((emp.id, name))
        return result

    first_name = fields.Char("Prénoms", required=False)
    category_id = fields.Many2one('hr.contract.category', 'Catégorie', required=False)
    type = fields.Selection([('h', 'Horaire'), ('j', 'Journalier'), ('m', 'Mensuel')], 'Type', required=False, default=False)
    matricule_cnps = fields.Char('N° CNPS', size=64)
    enfants_a_charge = fields.Integer("Nombre d'enfants à charge", required=True)
    part_igr = fields.Float(compute=_get_part_igr, string='Part IGR')
    start_date = fields.Date("Date d'ancienneté", required=True)
    seniority_employee = fields.Integer("Anciennété", compute="_get_seniority")
    end_date = fields.Date("Date de depart", required=False)
    age = fields.Integer('Âge employé', compute='_get_age_employee')
    total_children = fields.Integer('Nombre enfant total', compute='_compute_children')
    cmu_employe2 = fields.Integer(string='CMU employé', compute="_compute_children")
    cmu_employeur2 = fields.Integer(string='CMU employeur', compute="_compute_children")
    cmu_employe = fields.Integer(string='CMU employé', store=True, readonly=True)
    cmu_employeur = fields.Integer(store=True, readonly=True, string='CMU employeur')
    enfants_ids = fields.One2many('hr.employee.enfant', 'employee_id', 'Enfants', required=False)
    licence_ids = fields.One2many('hr.licence', 'employee_id', 'Licences des employés')
    diplome_ids = fields.One2many('hr.diplomes.employee', 'employee_id', 'Diplôme des employés')
    visa_ids = fields.One2many('hr.visa', 'employee_id', 'Visas des employés')
    carte_sejour_ids = fields.One2many('hr.carte.sejour', 'employee_id', 'Carte de séjour des employés')
    children = fields.Integer("Nombre d'enfant")
    date_entree = fields.Date("Date d'entrée")
    presonnes_contacted_ids = fields.One2many('hr.personne.contacted', 'employee_id', 'Personnes à contacter')
    parent_employee_ids = fields.One2many("hr.parent.employe", 'employee_id', 'Les parents')
    recruitment_degree_id = fields.Many2one('hr.employee.degree', "Niveau d'étude")
    direction_id = fields.Many2one('hr.department', 'Direction', required=False, domain="[('type', '=', 'direction')]")
    department_id = fields.Many2one('hr.department', 'Departement', required=False, domain="[('type', '=', 'department')]")
    service_id = fields.Many2one('hr.department', 'Service', domain="[('type', '=', 'service')]")
    conjoint_complete_name = fields.Char(string="Nom complet du conjoint(e)", groups="hr.group_hr_user")
    conjoint_birthdate = fields.Date(string="Date de naissance du conjoint", groups="hr.group_hr_user")
    nature_employe = fields.Selection([('local', 'Local'), ('expat', 'Expatrié')], "Nature de l'employé",
                                      default=False)
    num_cmu_conjoint = fields.Char('N° CMU conjoint', required=False)
    mode_paiement = fields.Selection([
        ('cheque', 'Chèque'),
        ('espece', 'Espèce'),
        ('virement', 'Virement'),
    ], 'Moyens de paiement')
    employee_id = fields.Char(string='Matricule No', groups="hr.group_hr_user", tracking=True)
    num_compte_bancaire = fields.Char("numéro de compte bancaire")
    num_secu_sociale = fields.Char("numéro de Sécurité Sociale")