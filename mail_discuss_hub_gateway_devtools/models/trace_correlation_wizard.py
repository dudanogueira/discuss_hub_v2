# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import _, fields, models
from odoo.exceptions import UserError


class TraceCorrelationWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.trace_correlation_wizard"
    _description = "Trace Correlation (dev tool)"

    log_id = fields.Many2one(
        "mail.gateway.webhook.log", string="Webhook Log", required=True
    )
    matched_message_ids = fields.Many2many(
        "mail.message",
        "mail_discuss_hub_dev_trace_message_rel",
        "wizard_id",
        "message_id",
        string="Messages",
        readonly=True,
    )
    matched_channel_id = fields.Many2one(
        "discuss.channel", string="Channel", readonly=True
    )
    matched_guest_id = fields.Many2one("mail.guest", string="Guest", readonly=True)
    correlation_strategy = fields.Char(string="Strategy", readonly=True)
    correlation_notes = fields.Text(string="Notes", readonly=True)

    def action_correlate(self):
        self.ensure_one()
        if not self._is_enabled():
            raise UserError(_("Trace correlation is disabled by Devtools settings."))

        self.write(
            {
                "matched_message_ids": [(5, 0, 0)],
                "matched_channel_id": False,
                "matched_guest_id": False,
                "correlation_strategy": False,
                "correlation_notes": False,
            }
        )

        notes = []
        strategies = []
        messages = self.env["mail.message"]

        direct_messages = self._find_by_log_link(self.log_id)
        if direct_messages:
            messages |= direct_messages
            strategies.append("gateway_webhook_log_id")
            notes.append(_("Matched via gateway_webhook_log_id."))

        if not messages:
            remote_messages = self._find_by_remote_id(self.log_id)
            if remote_messages:
                messages |= remote_messages
                strategies.append("gateway_remote_id")
                notes.append(_("Matched via (gateway_id, gateway_remote_id)."))

        channel = self._find_channel(messages) or self._find_channel_from_payload(self.log_id)
        guest = self._find_guest(messages) or self._find_guest_from_payload(self.log_id)

        self.write(
            {
                "matched_message_ids": [(6, 0, messages.ids)],
                "matched_channel_id": channel.id if channel else False,
                "matched_guest_id": guest.id if guest else False,
                "correlation_strategy": ", ".join(strategies) if strategies else "none",
                "correlation_notes": "\n".join(notes) if notes else _("No correlation found."),
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Trace Correlation"),
            "res_model": "mail_discuss_hub_dev.trace_correlation_wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def _find_by_log_link(self, log):
        if "gateway_webhook_log_id" not in self.env["mail.message"]._fields:
            return self.env["mail.message"]
        return (
            self.env["mail.message"]
            .sudo()
            .search([("gateway_webhook_log_id", "=", log.id)])
        )

    def _find_by_remote_id(self, log):
        if not log.gateway_id:
            return self.env["mail.message"]
        payload = self._parse_payload(log.request_payload)
        if not payload:
            return self.env["mail.message"]
        remote_id = self._extract_remote_id(payload)
        if not remote_id:
            return self.env["mail.message"]
        return (
            self.env["mail.message"]
            .sudo()
            .search(
                [
                    ("gateway_id", "=", log.gateway_id.id),
                    ("gateway_remote_id", "=", remote_id),
                ]
            )
        )

    def _find_channel(self, messages):
        for msg in messages:
            if msg.model == "discuss.channel" and msg.res_id:
                channel = self.env["discuss.channel"].sudo().browse(msg.res_id).exists()
                if channel:
                    return channel
        return False

    def _find_channel_from_payload(self, log):
        if not log.gateway_id:
            return False
        payload = self._parse_payload(log.request_payload)
        if not payload:
            return False
        chat_token = self._extract_chat_token(payload)
        if not chat_token:
            return False
        return (
            self.env["discuss.channel"]
            .sudo()
            .search(
                [
                    ("gateway_id", "=", log.gateway_id.id),
                    ("gateway_channel_token", "=", chat_token),
                ],
                limit=1,
            )
        )

    def _find_guest(self, messages):
        for msg in messages:
            guest = msg.sudo().author_guest_id
            if guest:
                return guest
        return False

    def _find_guest_from_payload(self, log):
        if not log.gateway_id:
            return False
        payload = self._parse_payload(log.request_payload)
        if not payload:
            return False
        sender_jid = self._extract_sender_jid(payload)
        if not sender_jid:
            return False
        return (
            self.env["mail.guest"]
            .sudo()
            .search(
                [
                    ("gateway_id", "=", log.gateway_id.id),
                    ("gateway_token", "=", str(sender_jid)),
                ],
                limit=1,
            )
        )

    @staticmethod
    def _parse_payload(raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    @staticmethod
    def _extract_remote_id(payload):
        data = payload.get("data") or {}
        key_data = data.get("key") or {}
        return key_data.get("id") or data.get("messageId")

    @staticmethod
    def _extract_chat_token(payload):
        data = payload.get("data") or {}
        key_data = data.get("key") or {}
        return key_data.get("remoteJid") or key_data.get("remoteJidAlt") or key_data.get("participant")

    @staticmethod
    def _extract_sender_jid(payload):
        data = payload.get("data") or {}
        key_data = data.get("key") or {}
        return key_data.get("participant") or key_data.get("remoteJid")

    def _is_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.trace_correlation_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")
