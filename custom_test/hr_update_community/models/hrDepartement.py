# -*- coding:utf-8 -*-

from odoo import api, fields, models, _

class HrDepartemet(models.Model):
    _inherit = "hr.department"

    type = fields.Selection([('direction', 'Direction'), ('department', 'Departement'), ('service', 'Service')], "Type")