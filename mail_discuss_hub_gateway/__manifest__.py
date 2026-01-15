# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Based on concepts from:
#   - https://github.com/discusshub/discuss_hub
#   - https://github.com/diegofrodrigues/wa_conn

{
    "name": "Mail Discuss Hub Gateway",
    "summary": "Discuss gateway extensions and sidebar grouping utilities",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Soloz Technologies",
    "contributors": [
        "DiscussHub Team <https://github.com/discusshub/discuss_hub>",
        "Diego Rodrigues <https://github.com/diegofrodrigues/wa_conn>",
    ],
    "website": "https://github.com/lcsztl/discuss_hub",
    "depends": ["mail_gateway", "mail_discuss_hub"],
    "data": [
        "views/discuss_channel_views.xml",
        "views/mail_discuss_hub_gateway_menus.xml",
        "data/cleanup_webhook_log_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mail_discuss_hub_gateway/static/src/js/gateway_instance_sidebar.esm.js",
            "mail_discuss_hub_gateway/static/src/js/message_author_fix.esm.js",
        ],
    },
    "installable": True,
}
