from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    gateway_message_external_id = fields.Char(index=True)
    gateway_instance = fields.Char(index=True)
    gateway_chat_id = fields.Char(index=True)
    gateway_sender_jid = fields.Char()
    gateway_sender_name = fields.Char()
    gateway_from_me = fields.Boolean()

    _sql_constraints = [
        (
            "gateway_message_external_id_unique",
            "unique(gateway_type, gateway_message_external_id, gateway_instance, gateway_chat_id)",
            "Gateway message already exists.",
        )
    ]
