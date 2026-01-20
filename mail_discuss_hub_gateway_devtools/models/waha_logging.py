# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class MailGatewayWhatsappWaha(models.AbstractModel):
    _inherit = "mail.gateway.whatsapp_waha"

    def _receive_update(self, gateway, update):
        log_record = self._devtools_log_webhook(
            gateway,
            direction="in",
            status="received",
            event=update.get("event") if isinstance(update, dict) else None,
            endpoint=self._devtools_inbound_endpoint(),
            payload=update,
        )
        dispatcher = self
        if log_record:
            dispatcher = dispatcher.with_context(gateway_webhook_log_id=log_record.id)
        try:
            result = super(MailGatewayWhatsappWaha, dispatcher)._receive_update(
                gateway, update
            ) or {}
        except Exception as exc:
            if log_record:
                log_record.sudo().write(
                    {
                        "status": "error",
                        "error_message": str(exc),
                    }
                )
            raise
        if log_record:
            status = (
                "processed"
                if result.get("status") in ("ok", "duplicate")
                else "received"
            )
            log_record.sudo().write({"status": status})
        return result

    @staticmethod
    def _devtools_inbound_endpoint():
        try:
            return request.httprequest.path
        except Exception:
            return False
