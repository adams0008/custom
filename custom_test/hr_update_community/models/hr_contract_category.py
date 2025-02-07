# -*- coding: utf-8 -*-

import time
from odoo import api, fields, osv, exceptions, models, _
from datetime import datetime

from dateutil import relativedelta


class hr_contract_category(models.Model):
    _name = 'hr.contract.category'
    _description = "Gestion des cetegories d'employee"
    _order = 'sequence'

    name = fields.Char('Désignation', required=True)
    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Séquence', required=True)
    description = fields.Text('Description', required=False)