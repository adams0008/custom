##############################################################################
#
# Copyright (c) 2024 2DAY GROUP - support@2daygroup.net
# Author: Himaf
#
# ##############################################################################
{
    "name" : "Mise à jour HR de Odoo",
    "version" : "1.0",
    "author" : "Himaf",
    "company": "2DAY GROUP",
    "maintainer": "2DAY GROUP",
    'category': 'Localization',
    "depends" : ["base", 'hr', 'hr_contract'],
    "description": """
    """,
    "data":[
            "security/ir.model.access.csv",
            #"views/res_config_settings_views.xml",
            "data/abatements_data.xml",
            "data/categories_employee_data.xml",
            "views/hr_category_employee_view.xml",
            "views/hr_category_salaire_view.xml",
            "views/res_company_view.xml",
            "views/res_partner_view.xml",
            "views/hr_employee_view.xml",
            "views/hrDepartmentView.xml",
        ],
    "web.assets_backend": [
            "/hr_update_community/static/src/legacy/scss/layout_style.scss",
        ],
    "installable": True
}
