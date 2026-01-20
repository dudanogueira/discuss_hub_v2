# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WahaWebhookEvent(models.Model):
    _name = "mail.gateway.whatsapp_waha.webhook_event"
    _description = "WAHA Webhook Event"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "mail_gateway_whatsapp_waha_event_code_unique",
            "unique(code)",
            "Event code must be unique.",
        ),
    ]
