# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Based on concepts from:
#   - https://github.com/discusshub/discuss_hub
#   - https://github.com/diegofrodrigues/wa_conn

{
    "name": "Mail Discuss Hub Core",
    "summary": "Discuss configuration menus for message administration",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "contributors": [
        "DiscussHub Team <https://github.com/discusshub/discuss_hub>",
        "Diego Rodrigues <https://github.com/diegofrodrigues/wa_conn>",
    ],
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/discuss_channel_views.xml",
        "views/mail_discuss_team_views.xml",
        "views/mail_discuss_team_menus.xml",
    ],
    "installable": True,
}
