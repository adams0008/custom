# -*- coding: utf-8 -*-
from num2words import num2words

from odoo import models, fields, api, exceptions, _
from PyPDF2 import PdfFileWriter, PdfFileReader
from odoo.tools.misc import format_date
from datetime import datetime, date
import time
import io
import base64
from dateutil.relativedelta import relativedelta


class NotificationConfiguration(models.Model):
    _name = "notify.configuration"

    name = fields.Char("Nom", required=True)
    day_before = fields.Integer("Nombre de jour avant notification", required=True)
    manager_id = fields.Many2one("res.users", "Manger RH", required=True)
    email_cc = fields.Many2many("res.users", string="Copie à")


class Notification(models.Model):
    _name = "notify.manager"

    def get_contract_end(self):
        contract_ids = self.env['hr.contract'].search([('state', '=', 'open')])
        notify_manager = self.env['notify.configuration'].search([])
        day_before = 0
        name = None
        email_to = None
        email_cc_ids = notify_manager.mapped("email_cc")
        email_cc = ''
        for cc in email_cc_ids:
            email_cc += cc.login + ';'
        for notify in notify_manager:
            day_before = notify.day_before
            name = notify.manager_id.name
            email_to = notify.manager_id.login
        for contract in contract_ids:
            if contract.date_end:
                today = datetime.now().strftime("%d-%m-%Y")
                if contract.date_end == today:
                    render_context = {
                        "name": name,
                        "employee": contract.employee_id.nom_adherent,
                        'contract_date': contract.date_end,
                        'numero_contrat': contract.name,
                    }
                    template = self.env.ref('hr_contract_extension_community.end_contract_mail_template')
                    mail_body = template.render(render_context, engine='ir.qweb', minimal_qcontext=True)

                    mail_id = self.env['mail.mail'].create({
                        'email_from': email_to,
                        'email_to': email_to,
                        'email_cc': email_cc,
                        'subject': 'Notification de fin de contrat',
                        'body_html': mail_body,
                    })
                    mail_id.send()
                if contract.date_end != today:
                    d = contract.date_end - relativedelta(months=day_before)
                    if d == today:
                        render_context = {
                            "name": name,
                            "employee": contract.employee_id.nom_adherent,
                            'contract_date': contract.date_end,
                            'numero_contrat': contract.name,
                        }
                        template = self.env.ref('hr_contract_extension_community.end_contract_mail_template')
                        mail_body = template.render(render_context, engine='ir.qweb', minimal_qcontext=True)

                        mail_id = self.env['mail.mail'].create({
                            'email_from': email_to,
                            'email_to': email_to,
                            'email_cc': email_cc,
                            'subject': 'Notification de fin de contrat',
                            'body_html': mail_body,
                        })
                        mail_id.send()
