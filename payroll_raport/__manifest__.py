# -*- coding: utf-8 -*-
##############################################################################
#
#    hr_payroll_ci_raport Odoo 8
#    Copyright (c) 2018 Copyright (c) 2018 aek
#      Anicet Eric Kouame <anicetkeric@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Les Rapports  de paie",
    "version": "1.0",
    "sequence": 1,
    "depends": ["payroll", 'hr'],
    "author": "Anicet Eric Kouame / Yoboue Parfait Alla / Hermann Kouadio/ Franck Amand/ Koné Adama",
    "category": "hr",
    "description": """
    This module provide :
    """,
    'data': [
        "security/ir.model.access.csv",
        "data/report_paperformat.xml",
        "rapports/report.xml",
        "views/report_payroll.xml",
        "views/hr_payroll_view.xml",
    ],
    'assets': {
        'web.assets_backend': [  # Ajouter votre JS au bundle backend
            'payroll_raport/static/src/js/action_excel.js'  # Chemin vers votre fichier JS
        ],
    },
    'installable': True,
    'active': False,
}