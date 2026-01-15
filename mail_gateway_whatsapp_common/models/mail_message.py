# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    gateway_id = fields.Many2one("mail.gateway", index=True)
    gateway_provider = fields.Char()
    gateway_instance = fields.Char()
    gateway_remote_id = fields.Char(index=True)
    gateway_chat_id = fields.Char()
    gateway_status = fields.Selection(
        [
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("read", "Read"),
            ("failed", "Failed"),
            ("deleted", "Deleted"),
        ],
        index=True,
    )
    gateway_status_raw = fields.Char()
    gateway_quoted_remote_id = fields.Char()
    gateway_has_reaction = fields.Boolean()
    gateway_deleted = fields.Boolean()
    gateway_payload_raw = fields.Text()

    _sql_constraints = [
        (
            "gateway_remote_unique",
            "unique(gateway_id, gateway_remote_id)",
            "Remote message id must be unique per gateway.",
        )
    ]
