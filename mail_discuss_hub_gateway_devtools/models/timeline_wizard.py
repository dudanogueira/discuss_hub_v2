# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import _, fields, models
from odoo.exceptions import UserError


class UnifiedTimelineWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.timeline_wizard"
    _description = "Unified Timeline (dev tool)"

    channel_id = fields.Many2one("discuss.channel", string="Channel")
    guest_id = fields.Many2one("mail.guest", string="Guest")
    line_ids = fields.One2many(
        "mail_discuss_hub_dev.timeline_line",
        "wizard_id",
        string="Timeline",
    )

    def action_build(self):
        self.ensure_one()
        if not self._is_timeline_enabled():
            raise UserError(_("Unified timeline is disabled by Devtools settings."))
        self.line_ids.unlink()
        channel = self._resolve_channel()
        if not channel:
            raise UserError(_("Select a Channel or a Guest linked to a channel."))

        lines = []
        lines += self._build_webhook_lines(channel)
        lines += self._build_message_lines(channel)
        lines.sort(key=lambda item: item["event_time"] or fields.Datetime.now())

        for sequence, values in enumerate(lines, start=1):
            values["sequence"] = sequence
            values["wizard_id"] = self.id
            self.env["mail_discuss_hub_dev.timeline_line"].create(values)

        return {
            "type": "ir.actions.act_window",
            "name": _("Unified Timeline"),
            "res_model": "mail_discuss_hub_dev.timeline_line",
            "view_mode": "list",
            "target": "current",
            "domain": [("wizard_id", "=", self.id)],
            "context": {"default_wizard_id": self.id},
        }

    def _is_timeline_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.unified_timeline_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    def _resolve_channel(self):
        if self.channel_id:
            return self.channel_id
        if not self.guest_id:
            return False
        if self.guest_id.gateway_id and self.guest_id.gateway_token:
            return self.env["discuss.channel"].search(
                [
                    ("gateway_id", "=", self.guest_id.gateway_id.id),
                    ("gateway_channel_token", "=", self.guest_id.gateway_token),
                ],
                limit=1,
            )
        return False

    def _build_webhook_lines(self, channel):
        domain = [("gateway_id", "=", channel.gateway_id.id)]
        logs = self.env["mail.gateway.webhook.log"].sudo().search(
            domain, order="create_date asc"
        )
        lines = []
        for log in logs:
            if not self._log_matches_channel(log, channel):
                continue
            lines.append(
                {
                    "event_time": log.create_date,
                    "source_type": "webhook",
                    "event": log.event or "",
                    "direction": log.direction or "",
                    "http_status": log.http_status or 0,
                    "title": _("Webhook: %s") % (log.event or "-"),
                    "details": log.endpoint or "",
                    "webhook_log_id": log.id,
                }
            )
        return lines

    def _build_message_lines(self, channel):
        domain = [
            ("model", "=", "discuss.channel"),
            ("res_id", "=", channel.id),
        ]
        messages = self.env["mail.message"].sudo().search(
            domain, order="date asc, id asc"
        )
        lines = []
        for msg in messages:
            lines.append(
                {
                    "event_time": msg.date or msg.create_date,
                    "source_type": "message",
                    "event": msg.message_type or "",
                    "direction": "out" if msg.author_id == self.env.user.partner_id else "in",
                    "http_status": 0,
                    "title": _("Message: %s") % (msg.author_id.name or "-"),
                    "details": (msg.body or "")[:200],
                    "message_id": msg.id,
                }
            )
        return lines

    def _log_matches_channel(self, log, channel):
        if not channel.gateway_channel_token:
            return True
        payload = self._parse_payload(log.request_payload)
        if not payload:
            return False
        token = self._extract_chat_token(payload)
        return token == channel.gateway_channel_token

    @staticmethod
    def _parse_payload(raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    @staticmethod
    def _extract_chat_token(payload):
        data = payload.get("data") or {}
        key_data = data.get("key") or {}
        for key in ("remoteJid", "remoteJidAlt", "participant"):
            value = key_data.get(key)
            if value:
                return value
        return False


class UnifiedTimelineLine(models.TransientModel):
    _name = "mail_discuss_hub_dev.timeline_line"
    _description = "Unified Timeline Line (dev tool)"

    wizard_id = fields.Many2one(
        "mail_discuss_hub_dev.timeline_wizard", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=1)
    event_time = fields.Datetime(string="Time")
    source_type = fields.Selection(
        [("webhook", "Webhook"), ("message", "Message")],
        required=True,
    )
    event = fields.Char()
    direction = fields.Char()
    http_status = fields.Integer()
    title = fields.Char()
    details = fields.Text()
    webhook_log_id = fields.Many2one("mail.gateway.webhook.log")
    message_id = fields.Many2one("mail.message")
