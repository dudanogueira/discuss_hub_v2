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

    def _message_reaction(self, content, action, partner, guest, store=None):
        res = super()._message_reaction(content, action, partner, guest, store=store)
        if self.env.context.get("gateway_reaction_inbound"):
            return res
        for message in self:
            if not message.gateway_type or not message.gateway_message_external_id:
                continue
            if message.model != "discuss.channel" or not message.res_id:
                continue
            channel = self.env["discuss.channel"].browse(message.res_id)
            gateway = channel.gateway_id if channel else False
            if not gateway or gateway.gateway_type != message.gateway_type:
                continue
            chat_id = message.gateway_chat_id or channel.gateway_channel_token
            instance = message.gateway_instance
            common = self.env["mail.gateway.whatsapp.common"]
            common._send_reaction_outbound(
                gateway,
                message=message,
                reaction=content,
                action=action,
                chat_id=chat_id,
                message_external_id=message.gateway_message_external_id,
                instance=instance,
            )
        return res
