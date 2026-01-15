# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import fields, models


class MailGatewayWebhookLog(models.Model):
    _inherit = "mail.gateway.webhook.log"

    request_payload_pretty = fields.Text(
        compute="_compute_pretty_payloads",
        readonly=True,
    )
    response_payload_pretty = fields.Text(
        compute="_compute_pretty_payloads",
        readonly=True,
    )

    def _compute_pretty_payloads(self):
        for record in self:
            record.request_payload_pretty = self._pretty_json(record.request_payload)
            record.response_payload_pretty = self._pretty_json(record.response_payload)

    @staticmethod
    def _pretty_json(raw_value):
        if not raw_value:
            return ""
        try:
            parsed = json.loads(raw_value)
        except Exception:
            return raw_value
        try:
            return json.dumps(parsed, ensure_ascii=True, indent=2, sort_keys=True)
        except Exception:
            return raw_value
