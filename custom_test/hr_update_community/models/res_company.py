#-*- coding:utf-8 -*-

from odoo import api, fields, models, exceptions, _


class ResAbatement(models.Model):
    _name = 'res.abatement'
    _description = "Gestion des abatements"

    name = fields.Char("Libellé", required=True)
    taux = fields.Float("Taux", required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')


class ResCompany(models.Model):
    _inherit = 'res.company'

    abatement_ids = fields.Many2many('res.abatement', 'abament_company_reel', 'company_id', 'abatement_id', 'Abatements')
    num_cnps = fields.Char("Numéro CNPS", required=True, default="N/A")
    num_contribuable = fields.Char("Numéro Contribuable", required=True, default="N/A")
    taux_accident_travail = fields.Float('Taux accident de travail')
    taux_cnps_employee_local = fields.Float('Taux CNPS employé local')
    taux_cnps_employe_expat = fields.Float('aux CNPS employé expatrié')
    taux_cnps_employer = fields.Float('Taux CNPS employeur')
    taux_prestation_familiale = fields.Float('Taux prestation familiale')
    taux_assurance_mater = fields.Float('Taux assurance maternité')
    taux_its = fields.Float('Taux ITS')
    taux_fdfp = fields.Float('Taux FDFP')
    taux_fdfp_fc = fields.Float('Taux FDFP FC')
    impot_service = fields.Char("Service d'assiette", required=False)
    max_age_child = fields.Integer('Aĝe maximal enfant à charge', default=21)
    max_assiette_cnps = fields.Float("Plafond regime de retraite mensuel", default=1647315)
    max_assiette_autre_contribution = fields.Float("Plafond regime autres contributions", default=70000)
    mobile = fields.Char("Téléphone cellulaire")
    parcelle = fields.Char("Parcelle")