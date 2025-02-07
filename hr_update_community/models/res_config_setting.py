# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_hr_holidays_auto = fields.Boolean(string="Attribution automatique de congés")
    module_hr_employee_birthday = fields.Boolean(string="Notification dates d'anniversaires")
