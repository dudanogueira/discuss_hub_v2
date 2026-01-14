# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Discuss Hub CRM",
    "summary": "CRM integration for Discuss Teams",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail_discuss_hub", "crm"],
    "post_init_hook": "post_init_hook",
    "data": [
        "views/crm_team_views.xml",
        "views/mail_discuss_team_views.xml",
    ],
    "installable": True,
}
