# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailNotification(models.Model):
    _inherit = "mail.notification"

    def send_gateway(self, auto_commit=False, raise_exception=False, parse_mode="HTML"):
        for record in self:
            channel = getattr(record, "gateway_channel_id", False)
            gateway = channel.gateway_id if channel else False
            if gateway and hasattr(gateway, "_reopen_channel_if_needed"):
                reopened_by = record.author_id or (
                    record.mail_message_id.author_id if record.mail_message_id else False
                )
                if not reopened_by:
                    reopened_by = self.env.user.partner_id
                gateway._reopen_channel_if_needed(channel, reopened_by=reopened_by)
        return super().send_gateway(
            auto_commit=auto_commit,
            raise_exception=raise_exception,
            parse_mode=parse_mode,
        )
