# -*- coding:utf-8 -*-
import io
import json
import xlsxwriter
from odoo import models
from odoo.tools import date_utils
from odoo import models, fields, api
from datetime import datetime,  date
import base64
import tempfile
import logging

_logger = logging.getLogger(__name__)

class PayrollReportWizard(models.TransientModel):
    _name = 'payroll.report.wizard'
    _description = 'Wizard pour générer le livre de paie'

    date_from = fields.Date(string='Date de début', required=True)
    date_to = fields.Date(string='Date de fin', required=True)
    orientation = fields.Selection([
        ('portrait', 'Portrait'),
        ('landscape', 'Paysage')
    ],  string='Orientation', default='landscape')

    def print_payroll_report(self):
        data = {
            'model': 'payroll.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('payroll_raport.report_hr_payroll').with_context(landscape=True).report_action(self, data=data)
    
    def payroll_book_report_excel(self):
        data = {
            'model': 'payroll.report.wizard',
            'form': self.read()[0]
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'payroll.report.wizard',
                'options': json.dumps(data,
                                        default=date_utils.json_default),
                'output_format': 'xlsx',
                'report_name': 'payroll_raport.report_payroll',
            },
            'report_type': 'xlsx',
        }
    

    def get_xlsx_report(self, data, response):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']

        # Récupérer les bulletins de paie dans la période donnée
        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to)
        ])

        # Récupérer les règles de paie apparaissant dans les lignes des bulletins de paie
        rules_to_display = set()
        rule_mapping = {}
        for payslip in payslips:
            for line in payslip.line_ids:
                if line.salary_rule_id.appears_on_payslip:
                    rules_to_display.add(line.salary_rule_id)
                    rule_mapping[line.salary_rule_id.id] = line.salary_rule_id

        # Trier les règles selon leur séquence
        sorted_rules = sorted(rules_to_display, key=lambda rule: rule.sequence)

        # Préparation du fichier Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Rapport de Paie")

        # Définition des formats de cellule
        cell_format = workbook.add_format({'font_size': 12, 'align': 'center', 'border': 1})
        header_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14, 'bg_color': '#D7E4BC', 'border': 1})
        title_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 20})
        yellow_format = workbook.add_format({'font_size': 12, 'align': 'center', 'border': 1, 'bg_color': '#FFFF00'})
        grey_format = workbook.add_format({'font_size': 12, 'align': 'center', 'border': 1, 'bg_color': '#D3D3D3'})
        red_format = workbook.add_format({'font_size': 12, 'align': 'center', 'border': 1, 'font_color': '#f90829'})

        # Récupérer les règles importantes avec un format spécifique
        important_rules = {
            (self.env.ref('payroll.hr_salary_rule_brut', raise_if_not_found=False) or
            self.env['hr.salary.rule'].search([('name', 'ilike', 'Total Brut Imposable')], limit=1)).id: yellow_format,
            
            (self.env.ref('payroll.hr_salary_rule_ret', raise_if_not_found=False) or
            self.env['hr.salary.rule'].search([('name', 'ilike', 'Total Retenues')], limit=1)).id: yellow_format,

            (self.env.ref('payroll.hr_salary_rule_pcomp', raise_if_not_found=False) or
            self.env['hr.salary.rule'].search([('name', 'ilike', 'Total Charges Patronales')], limit=1)).id: yellow_format,

            (self.env.ref('payroll.hr_salary_rule_c_pnimp', raise_if_not_found=False) or
            self.env['hr.salary.rule'].search([('name', 'ilike', 'Total Non Imposable')], limit=1)).id: yellow_format,

            (self.env.ref('payroll.hr_salary_rule_net', raise_if_not_found=False) or
            self.env['hr.salary.rule'].search([('name', 'ilike', 'Net')], limit=1)).id: grey_format,

            (self.env.ref('payroll.hr_salary_rule_prorata', raise_if_not_found=False) or
            self.env['hr.salary.rule'].search([('name', 'ilike', 'Déduction prorata brut imposable')], limit=1)).id: red_format
        }

        # Créer un dictionnaire pour stocker les montants agrégés par employé
        aggregated_data = {}
        for payslip in payslips:
            employee_name = payslip.employee_id.name
            if employee_name not in aggregated_data:
                aggregated_data[employee_name] = {rule.name: 0 for rule in sorted_rules}

            for line in payslip.line_ids:
                if line.salary_rule_id.appears_on_payslip:
                    rule_name = line.salary_rule_id.name
                    aggregated_data[employee_name][rule_name] += line.total

        # Récupération du logo de l'entreprise
        logo_binary = self.env.user.company_id.logo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(base64.b64decode(logo_binary))
            tmp_file_path = tmp_file.name

        # Insertion du logo dans la feuille
        sheet.merge_range('A1:D3', '', cell_format)
        sheet.insert_image('A1', tmp_file_path, {'x_scale': 0.1, 'y_scale': 0.1, 'x_offset': 15, 'y_offset': 5})

        # Titre du rapport
        sheet.merge_range('A5:R5', f'Rapport de Paie Excel du {date_from} au {date_to}', title_format)

        # Création de l'en-tête avec les noms des règles de paie triées par séquence
        sheet.write(6, 0, 'Employé', header_format)
        col = 1
        for rule in sorted_rules:
            rule_format = important_rules.get(rule.id, header_format)
            sheet.write(6, col, rule.name, rule_format)
            col += 1

        # Ajout des employés et des données
        row = 7
        for employee_name, rule_totals in aggregated_data.items():
            sheet.write(row, 0, employee_name, cell_format)
            col = 1
            for rule in sorted_rules:
                rule_name = rule.name
                line_total = rule_totals.get(rule_name, 0)
                rule_format = important_rules.get(rule.id, cell_format)
                sheet.write(row, col, line_total, rule_format)
                col += 1
            row += 1

        # Fermeture du workbook et écriture de la réponse
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        # Supprimer le fichier temporaire du logo
        import os
        os.remove(tmp_file_path)


class PayrollReport(models.Model):
    _name = 'payroll.report'
    _description = 'Payroll Report'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    line_ids = fields.One2many('payroll.report.line', 'report_id', string='Payroll Lines')

class PayrollReportLine(models.Model):
    _name = 'payroll.report.line'
    _description = 'Payroll Report Line'

    report_id = fields.Many2one('payroll.report', string='Report')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    salary_rule_ids = fields.One2many('payroll.salary.rule.line', 'report_line_id', string='Salary Rules')

class PayrollSalaryRuleLine(models.Model):
    _name = 'payroll.salary.rule.line'
    _description = 'Payroll Salary Rule Line'

    report_line_id = fields.Many2one('payroll.report.line', string='Payroll Report Line')
    rule_name = fields.Char(string='Rule Name')
    amount = fields.Float(string='Amount')
