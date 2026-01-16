# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import difflib
import html
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
    analysis_enabled = fields.Boolean(
        compute="_compute_webhook_analysis",
        readonly=True,
    )
    analysis_error = fields.Text(
        compute="_compute_webhook_analysis",
        readonly=True,
    )
    analysis_provider = fields.Char(
        compute="_compute_webhook_analysis",
        readonly=True,
    )
    analysis_normalized_payload = fields.Text(
        compute="_compute_webhook_analysis",
        readonly=True,
    )
    analysis_mapping = fields.Text(
        compute="_compute_webhook_analysis",
        readonly=True,
    )
    analysis_message_id = fields.Many2one(
        "mail.message",
        compute="_compute_webhook_analysis",
        readonly=True,
    )
    analysis_routine = fields.Char(
        compute="_compute_webhook_analysis",
        readonly=True,
    )
    analysis_mapping_table_html = fields.Html(
        compute="_compute_webhook_analysis",
        readonly=True,
        sanitize=False,
    )
    inspector_enabled = fields.Boolean(
        compute="_compute_payload_inspector",
        readonly=True,
    )
    inspector_error = fields.Text(
        compute="_compute_payload_inspector",
        readonly=True,
    )
    inspector_event = fields.Char(
        compute="_compute_payload_inspector",
        readonly=True,
    )
    inspector_missing_fields = fields.Text(
        compute="_compute_payload_inspector",
        readonly=True,
    )
    inspector_used_fields = fields.Text(
        compute="_compute_payload_inspector",
        readonly=True,
    )
    inspector_diff = fields.Text(
        compute="_compute_payload_inspector",
        readonly=True,
    )

    def _compute_pretty_payloads(self):
        for record in self:
            record.request_payload_pretty = self._pretty_json(record.request_payload)
            record.response_payload_pretty = self._pretty_json(record.response_payload)

    def _compute_webhook_analysis(self):
        for record in self:
            record.analysis_enabled = record._is_analysis_enabled()
            record.analysis_error = False
            record.analysis_provider = record.gateway_id.gateway_type or ""
            record.analysis_normalized_payload = False
            record.analysis_mapping = False
            record.analysis_message_id = record._find_related_message()
            record.analysis_routine = False
            record.analysis_mapping_table_html = False

            if not record.analysis_enabled:
                record.analysis_error = "Webhook analysis is disabled."
                continue

            payload = record._parse_request_payload()
            if payload is None:
                record.analysis_error = "Invalid JSON payload."
                continue

            if record.gateway_id.gateway_type == "whatsapp_evolution_api":
                record._build_evolution_analysis(payload)
            else:
                record.analysis_error = "Provider not supported for analysis."

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

    def _is_analysis_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.webhook_analysis_enabled", default="1"
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    def _parse_request_payload(self):
        if not self.request_payload:
            return None
        try:
            return json.loads(self.request_payload)
        except Exception:
            return None

    def _find_related_message(self):
        if "gateway_webhook_log_id" not in self.env["mail.message"]._fields:
            return False
        return (
            self.env["mail.message"]
            .sudo()
            .search([("gateway_webhook_log_id", "=", self.id)], limit=1)
        )

    def _build_evolution_analysis(self, payload):
        gateway = self.gateway_id
        model = self.env["mail.gateway.whatsapp_evolution_api"]
        try:
            dto = model._build_dto_from_evolution(payload, gateway, False)
        except Exception as exc:
            self.analysis_error = f"Failed to normalize: {exc}"
            return
        if not dto:
            self.analysis_error = "Normalization returned empty DTO."
            return

        try:
            self.analysis_normalized_payload = json.dumps(
                dto.to_dict(), ensure_ascii=True, indent=2, sort_keys=True
            )
        except Exception:
            self.analysis_normalized_payload = str(dto.to_dict())

        mapping = self._evolution_mapping(payload, gateway, dto)
        try:
            self.analysis_mapping = json.dumps(
                mapping, ensure_ascii=True, indent=2, sort_keys=True
            )
        except Exception:
            self.analysis_mapping = str(mapping)
        self.analysis_routine = self._resolve_routine(dto)
        self.analysis_mapping_table_html = self._build_mapping_table_html(
            payload, mapping, dto
        )

    def _evolution_mapping(self, payload, gateway, dto):
        data = payload.get("data", {}) or {}
        key_data = data.get("key", {}) or {}
        message = data.get("message", {}) or {}
        return [
            {
                "source_path": "gateway.gateway_type",
                "normalized_field": "provider",
                "value": dto.provider,
            },
            {
                "source_path": "gateway.evolution_instance|gateway.name",
                "normalized_field": "instance",
                "value": dto.instance,
            },
            {
                "source_path": "event",
                "normalized_field": "event",
                "value": dto.event,
            },
            {
                "source_path": "data.key.id",
                "normalized_field": "message_id",
                "value": key_data.get("id"),
            },
            {
                "source_path": "data.key.remoteJid|data.key.remoteJidAlt|data.key.participant",
                "normalized_field": "chat_id",
                "value": dto.chat_id,
            },
            {
                "source_path": "data.key.fromMe",
                "normalized_field": "from_me",
                "value": dto.from_me,
            },
            {
                "source_path": "data.key.participant|data.key.remoteJid",
                "normalized_field": "sender_jid",
                "value": dto.sender_jid,
            },
            {
                "source_path": "data.key.remoteJidAlt",
                "normalized_field": "sender_jid_alt",
                "value": dto.sender_jid_alt,
            },
            {
                "source_path": "data.key.participant",
                "normalized_field": "sender_participant_jid",
                "value": dto.sender_participant_jid,
            },
            {
                "source_path": "data.pushName",
                "normalized_field": "sender_name",
                "value": dto.sender_name,
            },
            {
                "source_path": "data.message.messageTimestamp|data.timestamp",
                "normalized_field": "timestamp",
                "value": dto.timestamp,
            },
            {
                "source_path": "data.message.messageType|data.message.type",
                "normalized_field": "message_type",
                "value": dto.message_type,
            },
            {
                "source_path": "data.message.conversation|data.message.extendedTextMessage.text|data.message.*.caption",
                "normalized_field": "text",
                "value": dto.text,
            },
            {
                "source_path": "data.message.caption",
                "normalized_field": "caption",
                "value": message.get("caption"),
            },
            {
                "source_path": "data.quotedMessage.stanzaId|data.quotedStanzaID",
                "normalized_field": "quote_id",
                "value": dto.quote_id,
            },
            {
                "source_path": "data.quotedMessage.text",
                "normalized_field": "quote_text",
                "value": dto.quote_text,
            },
            {
                "source_path": "data.reaction",
                "normalized_field": "reaction",
                "value": dto.reaction,
            },
            {
                "source_path": "data.reactionMessageId|data.messageId",
                "normalized_field": "reaction_target_id",
                "value": dto.reaction_target_id,
            },
            {
                "source_path": "data.status",
                "normalized_field": "status",
                "value": dto.status,
            },
            {
                "source_path": "data.status_raw",
                "normalized_field": "status_raw",
                "value": dto.status_raw,
            },
        ]

    def _build_mapping_table_html(self, payload, mapping, dto):
        mapping_by_source = self._mapping_index_by_source(mapping)
        dest_map = self._normalized_destination_map()
        rows = []
        seen_normalized = set()
        for raw_path, raw_value in self._flatten_payload(payload):
            entry = self._find_mapping_entry(raw_path, mapping_by_source)
            normalized_field = ""
            normalized_value = ""
            destination = ""
            if entry and raw_value is not None:
                normalized_field = entry.get("normalized_field") or ""
                normalized_value = entry.get("value")
                dest_model, dest_field = dest_map.get(normalized_field, ("", ""))
                destination = self._format_destination(dest_model, dest_field)
                if normalized_field:
                    seen_normalized.add(normalized_field)
            rows.append(
                {
                    "raw_path": raw_path,
                    "raw_value": self._format_value(raw_value),
                    "normalized_field": normalized_field,
                    "normalized_value": self._format_value(normalized_value),
                    "destination": destination,
                }
            )
        for normalized_field, (dest_model, dest_field) in dest_map.items():
            if normalized_field in seen_normalized:
                continue
            rows.append(
                {
                    "raw_path": "",
                    "raw_value": "",
                    "normalized_field": normalized_field,
                    "normalized_value": "",
                    "destination": self._format_destination(dest_model, dest_field),
                }
            )
        return self._render_mapping_table(rows)

    @staticmethod
    def _mapping_index_by_source(mapping):
        index = {}
        for entry in mapping:
            source_path = entry.get("source_path") or ""
            for part in source_path.split("|"):
                part = part.strip()
                if part:
                    index[part] = entry
        return index

    def _find_mapping_entry(self, raw_path, mapping_index):
        direct = mapping_index.get(raw_path)
        if direct:
            return direct
        normalized_path = self._strip_indexes(raw_path)
        direct = mapping_index.get(normalized_path)
        if direct:
            return direct
        for key, entry in mapping_index.items():
            if "*" not in key:
                continue
            if self._match_wildcard_path(normalized_path, key):
                return entry
        return False

    @staticmethod
    def _normalized_destination_map():
        return {
            "provider": ("mail.message", "gateway_provider"),
            "instance": ("mail.message", "gateway_instance"),
            "event": ("mail.gateway.whatsapp.common", "_process_normalized"),
            "message_id": ("mail.message", "gateway_remote_id"),
            "chat_id": ("mail.message", "gateway_chat_id"),
            "from_me": ("mail.guest/res.partner", "author"),
            "sender_jid": ("mail.guest", "gateway_token"),
            "sender_jid_alt": ("mail.guest", "whatsapp_remote_jid_alt"),
            "sender_participant_jid": ("mail.guest", "whatsapp_participant_jid"),
            "sender_name": ("mail.guest", "name/last_push_name"),
            "timestamp": ("mail.message", "date"),
            "message_type": ("mail.message", "message_type"),
            "text": ("mail.message", "body"),
            "caption": ("mail.message", "body"),
            "quote_id": ("mail.message", "gateway_quoted_remote_id"),
            "quote_text": ("mail.message", "parent_id/body"),
            "reaction": ("mail.message.reaction", "reaction"),
            "reaction_target_id": ("mail.message.reaction", "message_id"),
            "status": ("mail.message", "gateway_status"),
            "status_raw": ("mail.message", "gateway_status_raw"),
        }

    @staticmethod
    def _format_destination(model, field_name):
        if not model and not field_name:
            return ""
        if model and field_name:
            return f"{model}.{field_name}"
        return model or field_name

    @staticmethod
    def _format_value(value):
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=True, sort_keys=True)
            except Exception:
                return str(value)
        return str(value)

    @staticmethod
    def _render_mapping_table(rows):
        headers = ["Raw Path", "Raw Value", "Normalized", "Normalized Value", "Destination"]
        lines = [
            "<table class=\"table table-sm table-striped o_list_view\">",
            "<thead><tr>"
            + "".join(f"<th>{html.escape(header)}</th>" for header in headers)
            + "</tr></thead>",
            "<tbody>",
        ]
        for row in rows:
            lines.append(
                "<tr>"
                + f"<td><code>{html.escape(str(row.get('raw_path') or ''))}</code></td>"
                + f"<td>{html.escape(str(row.get('raw_value') or ''))}</td>"
                + f"<td>{html.escape(str(row.get('normalized_field') or ''))}</td>"
                + f"<td>{html.escape(str(row.get('normalized_value') or ''))}</td>"
                + f"<td><code>{html.escape(str(row.get('destination') or ''))}</code></td>"
                + "</tr>"
            )
        lines.append("</tbody></table>")
        return "\n".join(lines)

    @staticmethod
    def _resolve_routine(dto):
        event = (dto.event or "").lower()
        if event in {"message_upsert", "messages_upsert", "message"}:
            return "send_message" if dto.from_me else "receive_message"
        if event in {"message_status", "status"}:
            return "update_status"
        if event in {"message_delete", "delete"}:
            return "delete_message"
        if event in {"reaction_upsert", "reaction"}:
            return "add_reaction"
        if event in {"reaction_delete"}:
            return "remove_reaction"
        if event:
            return f"unhandled:{event}"
        return "unhandled"

    @staticmethod
    def _strip_indexes(path):
        result = ""
        skip = False
        for char in path:
            if char == "[":
                skip = True
                continue
            if char == "]":
                skip = False
                continue
            if not skip:
                result += char
        return result

    @staticmethod
    def _match_wildcard_path(value_path, pattern):
        value_parts = value_path.split(".")
        pattern_parts = pattern.split(".")
        if len(value_parts) != len(pattern_parts):
            return False
        for value_part, pattern_part in zip(value_parts, pattern_parts):
            if pattern_part == "*":
                continue
            if value_part != pattern_part:
                return False
        return True

    def _flatten_payload(self, payload, prefix=""):
        rows = []
        if isinstance(payload, dict):
            if not payload and prefix:
                rows.append((prefix, payload))
                return rows
            for key, value in payload.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                rows.extend(self._flatten_payload(value, path))
            return rows
        if isinstance(payload, list):
            if not payload and prefix:
                rows.append((prefix, payload))
                return rows
            for index, value in enumerate(payload):
                path = f"{prefix}[{index}]" if prefix else f"[{index}]"
                rows.extend(self._flatten_payload(value, path))
            return rows
        if prefix:
            rows.append((prefix, payload))
        return rows

    def _compute_payload_inspector(self):
        for record in self:
            record.inspector_enabled = record._is_payload_inspector_enabled()
            record.inspector_error = False
            record.inspector_event = False
            record.inspector_missing_fields = False
            record.inspector_used_fields = False
            record.inspector_diff = False

            if not record.inspector_enabled:
                record.inspector_error = "Payload inspector is disabled."
                continue

            payload = record._parse_request_payload()
            if payload is None:
                record.inspector_error = "Invalid JSON payload."
                continue

            record.inspector_event = payload.get("event") or ""
            if record.gateway_id.gateway_type == "whatsapp_evolution_api":
                if not record._evolution_payload_supports_message_fields(payload):
                    record.inspector_error = "Event payload is not message-based."
                    record.inspector_missing_fields = ""
                    record.inspector_used_fields = ""
                    record.inspector_diff = record._payload_diff(payload)
                    continue
                missing = record._evolution_missing_fields(payload)
                used = record._evolution_used_fields()
            else:
                record.inspector_error = "Provider not supported for inspector."
                continue

            record.inspector_missing_fields = record._pretty_json_list(missing)
            record.inspector_used_fields = record._pretty_json_list(used)
            record.inspector_diff = record._payload_diff(payload)

    def _is_payload_inspector_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.payload_inspector_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    @staticmethod
    def _pretty_json_list(values):
        if not values:
            return ""
        try:
            return json.dumps(values, ensure_ascii=True, indent=2, sort_keys=True)
        except Exception:
            return "\n".join([str(value) for value in values])

    @staticmethod
    def _get_path(payload, path):
        value = payload
        for part in path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value

    def _evolution_missing_fields(self, payload):
        missing = []
        if not payload.get("event"):
            missing.append("event")
        data = payload.get("data")
        if not data:
            missing.append("data")
            return missing
        if not isinstance(data, dict):
            missing.append("data (expected object)")
            return missing
        key_data = data.get("key") or {}
        if not key_data.get("id"):
            missing.append("data.key.id")
        if not (
            key_data.get("remoteJid")
            or key_data.get("remoteJidAlt")
            or key_data.get("participant")
        ):
            missing.append("data.key.remoteJid|data.key.remoteJidAlt|data.key.participant")
        if not data.get("message"):
            missing.append("data.message")
        return missing

    @staticmethod
    def _evolution_payload_supports_message_fields(payload):
        data = payload.get("data")
        if not isinstance(data, dict):
            return False
        if not data.get("message"):
            return False
        return True

    @staticmethod
    def _evolution_used_fields():
        return [
            "event",
            "data.key.id",
            "data.key.remoteJid",
            "data.key.remoteJidAlt",
            "data.key.participant",
            "data.key.fromMe",
            "data.pushName",
            "data.message.messageTimestamp",
            "data.timestamp",
            "data.message.messageType",
            "data.message.type",
            "data.message.conversation",
            "data.message.extendedTextMessage.text",
            "data.message.caption",
            "data.message.imageMessage.caption",
            "data.message.videoMessage.caption",
            "data.message.audioMessage",
            "data.message.documentMessage",
            "data.message.stickerMessage",
            "data.message.base64",
            "data.message.imageMessage.base64",
            "data.message.videoMessage.base64",
            "data.message.audioMessage.base64",
            "data.message.documentMessage.base64",
            "data.message.stickerMessage.base64",
            "data.message.imageMessage.mimetype",
            "data.message.videoMessage.mimetype",
            "data.message.audioMessage.mimetype",
            "data.message.documentMessage.mimetype",
            "data.message.stickerMessage.mimetype",
            "data.message.fileName",
            "data.quotedMessage.stanzaId",
            "data.quotedStanzaID",
            "data.quotedMessage.text",
            "data.reaction",
            "data.reactionMessageId",
            "data.messageId",
            "data.status",
            "data.status_raw",
        ]

    def _payload_diff(self, payload):
        previous = (
            self.env["mail.gateway.webhook.log"]
            .sudo()
            .search(
                [
                    ("id", "<", self.id),
                    ("gateway_id", "=", self.gateway_id.id),
                    ("event", "=", self.event),
                ],
                order="id desc",
                limit=1,
            )
        )
        if not previous:
            return ""
        try:
            current_pretty = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
        except Exception:
            current_pretty = str(payload)
        previous_pretty = previous.request_payload_pretty or ""
        if not previous_pretty:
            return ""
        diff = difflib.unified_diff(
            previous_pretty.splitlines(),
            current_pretty.splitlines(),
            fromfile=f"log_{previous.id}",
            tofile=f"log_{self.id}",
            lineterm="",
        )
        return "\n".join(diff)
