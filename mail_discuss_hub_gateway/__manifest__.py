# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Discuss Hub Gateway",
    "summary": "Discuss UI helpers for gateway channels",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail_gateway", "mail_gateway_whatsapp_common", "mail_discuss_hub"],
    "data": [
        "views/mail_gateway_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mail_discuss_hub_gateway/static/src/js/gateway_instance_sidebar.esm.js",
        ],
    },
    "installable": True,
}
