# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailGatewayWebhookLog(models.Model):
    _name = "mail.gateway.webhook.log"
    _description = "Gateway Webhook Log"
    _order = "create_date desc"

    gateway_id = fields.Many2one("mail.gateway", ondelete="set null")
    company_id = fields.Many2one(
        "res.company", related="gateway_id.company_id", store=True, readonly=True
    )
    gateway_type = fields.Selection(
        related="gateway_id.gateway_type", store=True, readonly=True
    )
    direction = fields.Selection(
        [
            ("in", "Inbound"),
            ("out", "Outbound"),
        ],
        required=True,
        default="in",
    )
    status = fields.Selection(
        [
            ("received", "Received"),
            ("processed", "Processed"),
            ("rejected", "Rejected"),
            ("sending", "Sending"),
            ("sent", "Sent"),
            ("error", "Error"),
        ],
        required=True,
        default="received",
    )
    event = fields.Char()
    endpoint = fields.Char()
    http_status = fields.Integer()
    request_payload = fields.Text()
    response_payload = fields.Text()
    error_message = fields.Text()
