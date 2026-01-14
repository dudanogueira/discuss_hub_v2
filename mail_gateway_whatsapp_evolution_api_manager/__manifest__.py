# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Based on concepts from:
#   - https://github.com/discusshub/discuss_hub
#   - https://github.com/diegofrodrigues/wa_conn
#   - https://github.com/gerencialp-bit/odoo-whatsapp-evolution-api

{
    "name": "Mail Gateway WhatsApp Evolution API Manager",
    "summary": "Manage Evolution API servers and instances",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "contributors": [
        "DiscussHub Team <https://github.com/discusshub/discuss_hub>",
        "Diego Rodrigues <https://github.com/diegofrodrigues/wa_conn>",
        "Gerencial P <https://github.com/gerencialp-bit/odoo-whatsapp-evolution-api>",
    ],
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail_gateway_whatsapp_evolution_api"],
    "assets": {
        "web.assets_backend": [
            "mail_gateway_whatsapp_evolution_api_manager/static/src/js/evolution_qr_code.esm.js",
            "mail_gateway_whatsapp_evolution_api_manager/static/src/xml/evolution_qr_code.xml",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/evolution_api_server_views.xml",
        "views/evolution_api_instance_views.xml",
        "views/evolution_api_menus.xml",
    ],
    "installable": True,
}
