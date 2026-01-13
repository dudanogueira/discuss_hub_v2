# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import uuid

from odoo import api, fields, models


class MailGateway(models.Model):
    _inherit = "mail.gateway"

    gateway_type = fields.Selection(
        selection_add=[
            ("whatsapp_evolution_api", "WhatsApp (Evolution API)"),
        ],
        ondelete={"whatsapp_evolution_api": "cascade"},
    )
    evolution_api_url = fields.Char(
        string="Evolution API URL",
        help="Base URL of the Evolution API server (ex: https://evolution.example.com)",
    )
    evolution_instance = fields.Char(
        string="Evolution Instance",
        help="Technical instance name in Evolution API. Defaults to the gateway name.",
    )
    evolution_base64_webhook = fields.Boolean(
        string="Webhook Base64",
        default=True,
        help="When enabled, Evolution will send media as base64 in webhooks.",
    )
    evolution_webhook_events = fields.Char(
        string="Webhook Events",
        default="MESSAGES_UPSERT,CONNECTION_UPDATE,QRCODE_UPDATED",
        help="Comma-separated list of Evolution webhook events to subscribe.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("evolution_api_url"):
                vals["evolution_api_url"] = vals["evolution_api_url"].rstrip("/")
            if (
                vals.get("gateway_type") == "whatsapp_evolution_api"
                and not vals.get("webhook_key")
            ):
                vals["webhook_key"] = str(uuid.uuid4())
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("evolution_api_url"):
            vals["evolution_api_url"] = vals["evolution_api_url"].rstrip("/")
        res = super().write(vals)
        if not self.env.context.get("skip_evolution_defaults"):
            for record in self.filtered(
                lambda r: r.gateway_type == "whatsapp_evolution_api" and not r.webhook_key
            ):
                record.with_context(skip_evolution_defaults=True).write(
                    {"webhook_key": str(uuid.uuid4())}
                )
        return res
