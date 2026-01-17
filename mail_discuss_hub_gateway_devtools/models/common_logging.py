# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailGatewayWhatsappCommon(models.AbstractModel):
    _inherit = "mail.gateway.whatsapp.common"

    def _process_normalized(self, gateway, dto, channel, author=None):
        result = super()._process_normalized(gateway, dto, channel, author=author)
        self._devtools_log_internal_result(dto, result)
        return result

    def _devtools_log_internal_result(self, dto, result):
        log_id = self.env.context.get("gateway_webhook_log_id")
        if not log_id:
            return
        if "mail.gateway.webhook.log" not in self.env:
            return
        log = self.env["mail.gateway.webhook.log"].sudo().browse(log_id).exists()
        if not log:
            return
        routine = log._resolve_routine(dto)
        status = result.get("status") if isinstance(result, dict) else None
        internal_result = (
            "processed" if status in ("ok", "duplicate") else "received"
        )
        log.write(
            {
                "internal_routine": routine,
                "internal_result": internal_result,
            }
        )
