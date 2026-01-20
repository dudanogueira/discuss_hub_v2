# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import models


class MailGatewayDevtoolsLogging(models.AbstractModel):
    _inherit = "mail.gateway.abstract"

    def _devtools_log_webhook(
        self,
        gateway,
        direction,
        status,
        payload=None,
        event=None,
        endpoint=None,
    ):
        if "mail.gateway.webhook.log" not in self.env:
            return False
        if not self._devtools_is_webhook_logging_enabled():
            return False
        payload_text = self._devtools_format_payload(payload)
        return (
            self.env["mail.gateway.webhook.log"]
            .sudo()
            .create(
                {
                    "gateway_id": gateway.id if gateway else False,
                    "direction": direction,
                    "status": status,
                    "event": event,
                    "endpoint": endpoint,
                    "request_payload": payload_text,
                }
            )
        )

    def _devtools_is_webhook_logging_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.webhook_log_enabled", default="1"
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    @staticmethod
    def _devtools_format_payload(payload):
        if payload is None:
            return False
        try:
            return json.dumps(payload, ensure_ascii=True, indent=2)
        except (TypeError, ValueError):
            return str(payload)
