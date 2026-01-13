# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Gateway WhatsApp Evolution API Manager",
    "summary": "Manage Evolution API servers and instances",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail_gateway_whatsapp_evolution_api"],
    "data": [
        "security/ir.model.access.csv",
        "views/evolution_api_server_views.xml",
        "views/evolution_api_instance_views.xml",
        "views/evolution_api_menus.xml",
    ],
    "installable": True,
}
