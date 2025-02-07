# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Veone - support.veone.net
# Author: KERYATEC
#
# Fichier du module hr_synthese
# ##############################################################################
{
    "name": "Extension du contrats",
    "version": "1.0",
    "author": "KERYATEC",
    'category': 'Human Resources',
    "website": "www.keryatec.com",
    "depends": ['base',"hr_contract", "hr_update_community"],
    "description": """ Extension du contrats de travail des employés
    """,
    "data": [
        "security/ir.model.access.csv",
        "data/primes_data.xml",
        "data/hr_categorie_salariale.xml",
        "data/mail_template.xml",
        "data/service_cron.xml",
        "views/hr_convention_view.xml",
        "views/hr_contract_view.xml",
        "views/hr_categorie_salairale_view.xml",
        "views/notify_end_contract.xml",
    ],
    "installable": True
}
