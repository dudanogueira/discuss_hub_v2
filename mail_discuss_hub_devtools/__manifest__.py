# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Discuss Hub Dev Tools",
    "summary": "Ferramentas tecnicas para desenvolvimento (webhook, replay, cleanup)",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": [
        "mail_gateway",
        "mail_discuss_hub",
        "mail_gateway_whatsapp_evolution_api_manager",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/webhook_log_base_views.xml",
        "views/mail_message_views.xml",
        "views/evolution_api_instance_views.xml",
        "views/dev_menus.xml",
        "views/webhook_log_views.xml",
        "wizards/webhook_replay_wizard.xml",
        "wizards/cleanup_wizard.xml",
    ],
    "installable": True,
}
