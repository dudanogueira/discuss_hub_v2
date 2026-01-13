# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Discuss Hub Gateway",
    "summary": "Discuss gateway extensions and sidebar grouping utilities",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail_gateway", "mail_discuss_hub"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/mail_gateway_webhook_log.xml",
        "views/mail_discuss_hub_gateway_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mail_discuss_hub_gateway/static/src/js/gateway_instance_sidebar.esm.js",
            "mail_discuss_hub_gateway/static/src/js/message_author_fix.esm.js",
        ],
    },
    "installable": True,
}
