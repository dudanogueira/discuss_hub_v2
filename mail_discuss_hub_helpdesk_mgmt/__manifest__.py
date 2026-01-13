# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Discuss Hub Helpdesk Mgmt",
    "summary": "Helpdesk Mgmt integration for Discuss Teams",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail_discuss_hub", "helpdesk_mgmt"],
    "data": [
        "views/mail_discuss_team_views.xml",
        "views/helpdesk_ticket_team_views.xml",
    ],
    "installable": True,
}
