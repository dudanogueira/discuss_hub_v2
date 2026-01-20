from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    _gateway_status_selection = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
        ("failed", "Failed"),
    ]

    gateway_message_external_id = fields.Char(index=True)
    gateway_instance = fields.Char(index=True)
    gateway_chat_id = fields.Char(index=True)
    gateway_message_key = fields.Char(index=True)
    gateway_sender_jid = fields.Char()
    gateway_sender_name = fields.Char()
    gateway_from_me = fields.Boolean()
    gateway_message_status = fields.Selection(_gateway_status_selection, index=True)
    gateway_message_status_raw = fields.Char()
    gateway_quote_external_id = fields.Char(index=True)
    gateway_quote_text = fields.Text()
    gateway_is_deleted = fields.Boolean(default=False)
    gateway_deleted_at = fields.Datetime()

    _sql_constraints = [
        (
            "gateway_message_key_unique",
            "unique(gateway_message_key)",
            "Gateway message already exists.",
        )
    ]
