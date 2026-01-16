# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    gateway_payload_raw = fields.Text(
        help="Raw payload captured during processing (dev-only)."
    )

    gateway_webhook_log_id = fields.Many2one(
        "mail.gateway.webhook.log",
        string="Webhook Log",
        ondelete="set null",
        copy=False,
    )
    gateway_webhook_direction = fields.Selection(
        related="gateway_webhook_log_id.direction", readonly=True
    )
    gateway_webhook_status = fields.Selection(
        related="gateway_webhook_log_id.status", readonly=True
    )
    gateway_webhook_event = fields.Char(
        related="gateway_webhook_log_id.event", readonly=True
    )
    gateway_webhook_endpoint = fields.Char(
        related="gateway_webhook_log_id.endpoint", readonly=True
    )
    gateway_webhook_http_status = fields.Integer(
        related="gateway_webhook_log_id.http_status", readonly=True
    )
    gateway_webhook_request_payload = fields.Text(
        related="gateway_webhook_log_id.request_payload", readonly=True
    )
    gateway_webhook_response_payload = fields.Text(
        related="gateway_webhook_log_id.response_payload", readonly=True
    )
    gateway_webhook_error_message = fields.Text(
        related="gateway_webhook_log_id.error_message", readonly=True
    )
