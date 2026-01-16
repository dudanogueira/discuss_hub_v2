# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class GapChecklistWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.gap_checklist_wizard"
    _description = "Gap Checklist (dev tool)"

    provider = fields.Selection(
        [
            ("whatsapp_evolution_api", "Evolution API"),
            ("all", "All Providers"),
        ],
        default="whatsapp_evolution_api",
        required=True,
    )
    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    direction = fields.Selection(
        [
            ("in", "Inbound"),
            ("out", "Outbound"),
            ("all", "All"),
        ],
        default="in",
        required=True,
    )
    date_from = fields.Datetime(string="From")
    date_to = fields.Datetime(string="To")
    line_ids = fields.One2many(
        "mail_discuss_hub_dev.gap_checklist_line",
        "wizard_id",
        string="Gap Lines",
    )

    def action_build(self):
        self.ensure_one()
        if not self._is_enabled():
            raise UserError(_("Gap checklist is disabled by Devtools settings."))

        self.line_ids.unlink()
        lines = self._build_gaps()
        line_model = self.env["mail_discuss_hub_dev.gap_checklist_line"]
        for line in lines:
            line["wizard_id"] = self.id
            line_model.create(line)

        return {
            "type": "ir.actions.act_window",
            "name": _( "Gap Checklist"),
            "res_model": "mail_discuss_hub_dev.gap_checklist_line",
            "view_mode": "list,form",
            "target": "current",
            "domain": [("wizard_id", "=", self.id)],
            "context": {"default_wizard_id": self.id},
        }

    def _build_gaps(self):
        log_model = self.env["mail.gateway.webhook.log"].sudo()
        domain = self._log_domain()
        logs = log_model.search(domain)

        supported_by_provider = self._supported_events_by_provider()
        known_labels_by_provider = self._known_event_labels_by_provider()
        todo_by_provider = self._todo_map_by_provider()

        gaps = {}
        for log in logs:
            provider_key = self._resolve_provider(log.gateway_type)
            normalized_event = self._normalize_event(log.event) or "unknown"
            supported = supported_by_provider.get(provider_key, set())
            if normalized_event in supported:
                continue

            key = (provider_key, normalized_event)
            if key not in gaps:
                gaps[key] = {
                    "gateway_type": provider_key or False,
                    "event_key": normalized_event,
                    "event_label": self._label_for_event(
                        normalized_event,
                        provider_key,
                        known_labels_by_provider,
                    ),
                    "event_raw_sample": log.event,
                    "count": 0,
                    "last_seen": log.create_date,
                    "last_log_id": log.id,
                    "priority": "low",
                    "todo_ref": todo_by_provider.get(provider_key, {}).get(normalized_event),
                    "todo_url": False,
                }
            entry = gaps[key]
            entry["count"] += 1
            if log.create_date and (not entry["last_seen"] or log.create_date > entry["last_seen"]):
                entry["last_seen"] = log.create_date
                entry["last_log_id"] = log.id
                entry["event_raw_sample"] = log.event

        for entry in gaps.values():
            entry["priority"] = self._priority_for_gap(entry["count"], entry["last_seen"])

        return sorted(
            gaps.values(),
            key=lambda item: (item["priority"], item["count"]),
            reverse=True,
        )

    def _log_domain(self):
        domain = []
        if self.gateway_id:
            domain.append(("gateway_id", "=", self.gateway_id.id))
        provider_key = self._selected_provider()
        if provider_key and provider_key != "all":
            domain.append(("gateway_type", "=", provider_key))
        if self.direction and self.direction != "all":
            domain.append(("direction", "=", self.direction))
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("create_date", "<=", self.date_to))
        return domain

    def _selected_provider(self):
        if self.gateway_id and self.gateway_id.gateway_type:
            return self.gateway_id.gateway_type
        return self.provider

    def _resolve_provider(self, gateway_type):
        if self.provider != "all":
            return self.provider
        return gateway_type or "unknown"

    def _supported_events_by_provider(self):
        return {
            "whatsapp_evolution_api": {
                "messages.upsert",
                "send.message",
            },
        }

    def _known_event_labels_by_provider(self):
        labels = {
            "whatsapp_evolution_api": {},
        }
        if "mail.gateway.whatsapp_evolution_api.webhook_event" in self.env:
            records = (
                self.env["mail.gateway.whatsapp_evolution_api.webhook_event"].sudo().search([])
            )
            for record in records:
                normalized = self._normalize_event(record.code)
                if not normalized:
                    continue
                labels.setdefault("whatsapp_evolution_api", {})[normalized] = record.name
        return labels

    def _todo_map_by_provider(self):
        return {
            "whatsapp_evolution_api": {
                "messages.update": "TODO-MESSAGES-UPDATE",
                "messages.delete": "TODO-MESSAGES-DELETE",
                "messages.set": "TODO-MESSAGES-SET",
                "contacts.update": "TODO-CONTACTS-UPDATE",
                "groups.upsert": "TODO-GROUPS-UPSERT",
                "group.participants.update": "TODO-GROUP-PARTICIPANTS",
                "connection.update": "TODO-CONNECTION-UPDATE",
                "presence.update": "TODO-PRESENCE-UPDATE",
                "labels.edit": "TODO-LABELS-EDIT",
            }
        }

    def _label_for_event(self, event_key, provider_key, labels_by_provider):
        label = labels_by_provider.get(provider_key, {}).get(event_key)
        if label:
            return label
        if not event_key:
            return "Unknown"
        return event_key.replace(".", " ").replace("_", " ").title()

    def _priority_for_gap(self, count, last_seen):
        if not last_seen:
            return "low"
        now = fields.Datetime.now()
        age = now - last_seen if now and last_seen else timedelta(days=999)
        if count >= 50 or age <= timedelta(days=1):
            return "high"
        if count >= 10 or age <= timedelta(days=7):
            return "medium"
        return "low"

    def _normalize_event(self, event):
        if not event:
            return ""
        return str(event).strip().lower().replace("_", ".")

    def _is_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.gap_checklist_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")


class GapChecklistLine(models.TransientModel):
    _name = "mail_discuss_hub_dev.gap_checklist_line"
    _description = "Gap Checklist Line (dev tool)"

    wizard_id = fields.Many2one(
        "mail_discuss_hub_dev.gap_checklist_wizard",
        required=True,
        ondelete="cascade",
    )
    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    gateway_type = fields.Char(string="Provider")
    event_key = fields.Char(string="Event Key")
    event_label = fields.Char(string="Event")
    event_raw_sample = fields.Char(string="Sample Event")
    count = fields.Integer(string="Count")
    last_seen = fields.Datetime(string="Last Seen")
    last_log_id = fields.Many2one(
        "mail.gateway.webhook.log",
        string="Last Log",
    )
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Priority",
    )
    todo_ref = fields.Char(string="TODO Ref")
    todo_url = fields.Char(string="TODO URL")
