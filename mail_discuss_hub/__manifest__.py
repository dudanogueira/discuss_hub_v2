# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Discuss Hub Core",
    "summary": "Discuss configuration menus for message administration",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/mail_discuss_team_views.xml",
        "views/mail_discuss_hub_menus.xml",
    ],
    "installable": True,
}
