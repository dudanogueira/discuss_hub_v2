# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailNotification(models.Model):
    _inherit = "mail.notification"

    def send_gateway(self, auto_commit=False, raise_exception=False, parse_mode="HTML"):
        common = self.env["mail.gateway.whatsapp.common"]

        def _use_common(record):
            channel = record.gateway_channel_id
            gateway = channel.gateway_id if channel else False
            return common._get_outbound_provider(gateway) is not False

        common_records = self.filtered(_use_common)
        if common_records:
            for record in common_records:
                gateway = record.gateway_channel_id.gateway_id
                common._send_outbound(
                    gateway,
                    record,
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    parse_mode=parse_mode,
                )
        remaining = self - common_records
        if remaining:
            return super(MailNotification, remaining).send_gateway(
                auto_commit=auto_commit,
                raise_exception=raise_exception,
                parse_mode=parse_mode,
            )
        return True
