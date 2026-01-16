# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import _, fields, models
from odoo.exceptions import UserError


class IdempotencyMapWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.idempotency_map_wizard"
    _description = "Idempotency Map (dev tool)"

    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    date_from = fields.Datetime(string="From")
    date_to = fields.Datetime(string="To")
    include_logs = fields.Boolean(string="Include Webhook Logs", default=True)
    include_messages = fields.Boolean(string="Include Messages", default=True)
    only_collisions = fields.Boolean(string="Only Collisions", default=False)
    line_ids = fields.One2many(
        "mail_discuss_hub_dev.idempotency_map_line",
        "wizard_id",
        string="Lines",
    )

    def action_build(self):
        self.ensure_one()
        if not self._is_enabled():
            raise UserError(_("Idempotency map is disabled by Devtools settings."))

        self.line_ids.unlink()
        entries = {}

        if self.include_logs:
            for log in self._fetch_logs():
                remote_id = self._extract_remote_id(log)
                if not remote_id:
                    continue
                key = (log.gateway_id.id, remote_id)
                entry = entries.setdefault(
                    key,
                    {
                        "gateway_id": log.gateway_id,
                        "gateway_remote_id": remote_id,
                        "log_ids": [],
                        "message_ids": [],
                        "events": set(),
                    },
                )
                entry["log_ids"].append(log.id)
                if log.event:
                    entry["events"].add(log.event)

        if self.include_messages:
            for msg in self._fetch_messages():
                if not msg.gateway_id or not msg.gateway_remote_id:
                    continue
                key = (msg.gateway_id.id, msg.gateway_remote_id)
                entry = entries.setdefault(
                    key,
                    {
                        "gateway_id": msg.gateway_id,
                        "gateway_remote_id": msg.gateway_remote_id,
                        "log_ids": [],
                        "message_ids": [],
                        "events": set(),
                    },
                )
                entry["message_ids"].append(msg.id)

        line_model = self.env["mail_discuss_hub_dev.idempotency_map_line"]
        for entry in entries.values():
            log_count = len(entry["log_ids"])
            message_count = len(entry["message_ids"])
            is_collision = log_count > 1 or message_count > 1
            if self.only_collisions and not is_collision:
                continue

            status = self._compute_status(log_count, message_count, is_collision)
            event_summary = ", ".join(sorted(entry["events"])) if entry["events"] else ""
            details = self._build_details(entry["log_ids"], entry["message_ids"])
            values = {
                "wizard_id": self.id,
                "gateway_id": entry["gateway_id"].id if entry["gateway_id"] else False,
                "gateway_remote_id": entry["gateway_remote_id"],
                "status": status,
                "log_count": log_count,
                "message_count": message_count,
                "event_summary": event_summary,
                "details": details,
                "is_collision": is_collision,
                "webhook_log_ids": [(6, 0, entry["log_ids"])],
                "message_ids": [(6, 0, entry["message_ids"])],
                "message_id": entry["message_ids"][0] if entry["message_ids"] else False,
            }
            line_model.create(values)

        return {
            "type": "ir.actions.act_window",
            "name": _("Idempotency Map"),
            "res_model": "mail_discuss_hub_dev.idempotency_map_line",
            "view_mode": "list,form",
            "target": "current",
            "domain": [("wizard_id", "=", self.id)],
            "context": {"default_wizard_id": self.id},
        }

    def _is_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.idempotency_map_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    def _fetch_logs(self):
        domain = []
        if self.gateway_id:
            domain.append(("gateway_id", "=", self.gateway_id.id))
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("create_date", "<=", self.date_to))
        return self.env["mail.gateway.webhook.log"].sudo().search(domain)

    def _fetch_messages(self):
        domain = [("gateway_remote_id", "!=", False)]
        if self.gateway_id:
            domain.append(("gateway_id", "=", self.gateway_id.id))
        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.date_to:
            domain.append(("date", "<=", self.date_to))
        return self.env["mail.message"].sudo().search(domain)

    def _extract_remote_id(self, log):
        payload = self._parse_payload(log.request_payload)
        if not payload:
            return False
        if log.gateway_id.gateway_type == "whatsapp_evolution_api":
            try:
                dto = self.env["mail.gateway.whatsapp_evolution_api"]._build_dto_from_evolution(
                    payload, log.gateway_id, False
                )
            except Exception:
                dto = False
            if dto and dto.message_id:
                return dto.message_id
        data = payload.get("data") or {}
        key_data = data.get("key") or {}
        return key_data.get("id") or data.get("messageId")

    @staticmethod
    def _parse_payload(raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    @staticmethod
    def _compute_status(log_count, message_count, is_collision):
        if message_count and log_count:
            return "collision" if is_collision else "ok"
        if log_count and not message_count:
            return "log_only"
        if message_count and not log_count:
            return "message_only"
        return "unknown"

    @staticmethod
    def _build_details(log_ids, message_ids):
        log_part = ", ".join(str(value) for value in log_ids) or "-"
        msg_part = ", ".join(str(value) for value in message_ids) or "-"
        return f"logs: {log_part}\nmessages: {msg_part}"


class IdempotencyMapLine(models.TransientModel):
    _name = "mail_discuss_hub_dev.idempotency_map_line"
    _description = "Idempotency Map Line (dev tool)"

    wizard_id = fields.Many2one(
        "mail_discuss_hub_dev.idempotency_map_wizard",
        required=True,
        ondelete="cascade",
    )
    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    gateway_remote_id = fields.Char(string="Remote ID")
    status = fields.Selection(
        [
            ("ok", "OK"),
            ("collision", "Collision"),
            ("log_only", "Log Only"),
            ("message_only", "Message Only"),
            ("unknown", "Unknown"),
        ],
        string="Status",
    )
    log_count = fields.Integer(string="Log Count")
    message_count = fields.Integer(string="Message Count")
    event_summary = fields.Char(string="Events")
    details = fields.Text()
    is_collision = fields.Boolean(string="Collision")
    webhook_log_ids = fields.Many2many(
        "mail.gateway.webhook.log",
        "mail_discuss_hub_dev_idem_log_rel",
        "line_id",
        "log_id",
        string="Webhook Logs",
    )
    message_ids = fields.Many2many(
        "mail.message",
        "mail_discuss_hub_dev_idem_msg_rel",
        "line_id",
        "message_id",
        string="Messages",
    )
    message_id = fields.Many2one("mail.message", string="Message")
