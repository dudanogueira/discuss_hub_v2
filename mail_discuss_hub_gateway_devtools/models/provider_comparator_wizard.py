# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import difflib
import json

from odoo import _, fields, models
from odoo.exceptions import UserError


class ProviderComparatorWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.provider_comparator_wizard"
    _description = "Provider Comparator (dev tool)"

    left_log_id = fields.Many2one(
        "mail.gateway.webhook.log", string="Left Log", required=True
    )
    right_log_id = fields.Many2one(
        "mail.gateway.webhook.log", string="Right Log", required=True
    )
    left_event = fields.Char(
        related="left_log_id.event", readonly=True, string="Left Event"
    )
    right_event = fields.Char(
        related="right_log_id.event", readonly=True, string="Right Event"
    )
    left_gateway_type = fields.Selection(
        related="left_log_id.gateway_type", readonly=True, string="Left Gateway Type"
    )
    right_gateway_type = fields.Selection(
        related="right_log_id.gateway_type", readonly=True, string="Right Gateway Type"
    )
    left_normalized = fields.Text(readonly=True)
    right_normalized = fields.Text(readonly=True)
    diff_text = fields.Text(readonly=True)
    notes = fields.Text(readonly=True)

    def action_compare(self):
        self.ensure_one()
        if not self._is_enabled():
            raise UserError(_("Provider comparator is disabled by Devtools settings."))

        left_payload, left_note = self._normalize_log(self.left_log_id)
        right_payload, right_note = self._normalize_log(self.right_log_id)

        left_json = self._to_json(left_payload)
        right_json = self._to_json(right_payload)
        diff = "\n".join(
            difflib.unified_diff(
                left_json.splitlines(),
                right_json.splitlines(),
                fromfile="left",
                tofile="right",
                lineterm="",
            )
        )
        notes = "\n".join(
            item for item in [left_note, right_note, self._diff_summary(left_payload, right_payload)] if item
        )

        self.write(
            {
                "left_normalized": left_json,
                "right_normalized": right_json,
                "diff_text": diff or "No differences.",
                "notes": notes,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Provider Comparator"),
            "res_model": "mail_discuss_hub_dev.provider_comparator_wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def _normalize_log(self, log):
        payload = self._parse_payload(log.request_payload)
        if not payload:
            return {}, _("Invalid JSON payload.")
        gateway = log.gateway_id
        if gateway and gateway.gateway_type == "whatsapp_evolution_api":
            try:
                dto = self.env["mail.gateway.whatsapp_evolution_api"]._build_dto_from_evolution(
                    payload, gateway, False
                )
            except Exception as exc:
                return {}, _("Evolution normalization failed: %s") % exc
            if not dto:
                return {}, _("Evolution normalization returned empty DTO.")
            return dto.to_dict(), ""
        return payload, _("No adapter for %s. Showing raw payload.") % (gateway.gateway_type or "unknown")

    @staticmethod
    def _parse_payload(raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    @staticmethod
    def _to_json(payload):
        try:
            return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
        except Exception:
            return str(payload)

    @staticmethod
    def _diff_summary(left_payload, right_payload):
        if not isinstance(left_payload, dict) or not isinstance(right_payload, dict):
            return ""
        left_keys = set(left_payload.keys())
        right_keys = set(right_payload.keys())
        added = sorted(right_keys - left_keys)
        removed = sorted(left_keys - right_keys)
        changed = sorted(
            key for key in left_keys & right_keys if left_payload.get(key) != right_payload.get(key)
        )
        parts = []
        if added:
            parts.append("added: " + ", ".join(added))
        if removed:
            parts.append("removed: " + ", ".join(removed))
        if changed:
            parts.append("changed: " + ", ".join(changed))
        return "Field differences: " + " | ".join(parts) if parts else ""

    def _is_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.provider_comparator_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")
