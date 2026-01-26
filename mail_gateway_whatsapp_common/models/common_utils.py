import re
from datetime import datetime
from markupsafe import Markup
from odoo import fields
from odoo.tools import html_escape

class MailGatewayWhatsappCommonUtils:
    def _apply_message_timestamp(self, message, dto):
        """Apply gateway timestamps to preserve chronological ordering."""
        if not message or not dto or not dto.timestamp:
            return
        dt_value = self._normalize_timestamp(dto.timestamp)
        if not dt_value:
            return
        message.sudo().write({"date": dt_value, "write_date": dt_value})
        self._apply_message_create_date(message, dt_value)


    def _render_message_body(self, dto):
        text = (dto.text or "").strip()
        if not text:
            text = (dto.caption or "").strip()
        if not text:
            return ""
        if dto.text_is_html:
            return Markup(text)
        text = self._br_tag_re.sub("\n", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        escaped = html_escape(text)
        return Markup(escaped.replace("\n", Markup("<br/>")))


    def _normalize_timestamp(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return fields.Datetime.from_timestamp(self._normalize_epoch(value))
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return False
            if value.isdigit():
                return fields.Datetime.from_timestamp(self._normalize_epoch(int(value)))
            try:
                float_value = float(value)
            except ValueError:
                float_value = None
            if float_value is not None:
                return fields.Datetime.from_timestamp(self._normalize_epoch(float_value))
            try:
                return fields.Datetime.to_datetime(value)
            except Exception:
                return False
        return False


    def _normalize_epoch(self, value):
        if value is None:
            return value
        if value > 1e11:
            return value / 1000.0
        return value


    def _apply_message_create_date(self, message, dt_value):
        if not message or not dt_value:
            return
        if message.create_date and message.create_date == dt_value:
            return
        try:
            # Direct SQL is needed to update create_date without side effects.
            self.env.cr.execute(
                "UPDATE mail_message SET create_date=%s WHERE id=%s",
                (fields.Datetime.to_string(dt_value), message.id),
            )
            message.invalidate_recordset(["create_date"])
        except Exception:
            self._logger.debug("Failed to update mail.message create_date.", exc_info=True)


    def _find_message_by_external_id(
        self, gateway, message_id, chat_id=None, instance=None
    ):
        message_id = (message_id or "").strip()
        if not message_id:
            return False
        message_model = self.env["mail.message"].sudo()
        if "gateway_message_key" in message_model._fields and gateway:
            key = self._build_message_key_from_values(
                gateway, instance, chat_id, message_id
            )
            if key:
                existing = message_model.search(
                    [("gateway_message_key", "=", key)], limit=1
                )
                if existing:
                    return existing
        if "gateway_message_external_id" not in message_model._fields:
            return False
        domain = [("gateway_message_external_id", "=", message_id)]
        if "gateway_type" in message_model._fields and gateway:
            domain.append(("gateway_type", "=", gateway.gateway_type))
        if instance and "gateway_instance" in message_model._fields:
            domain.append(("gateway_instance", "=", instance))
        if chat_id and "gateway_chat_id" in message_model._fields:
            domain.append(("gateway_chat_id", "=", chat_id))
        return message_model.search(domain, limit=1)


    def _find_existing_message(self, gateway, dto, message_key=None):
        # Prefer gateway_message_key for strict idempotency when available.
        message_model = self.env["mail.message"].sudo()
        if "gateway_message_key" in message_model._fields:
            message_key = message_key or self._build_message_key(gateway, dto)
            if message_key:
                existing = message_model.search(
                    [("gateway_message_key", "=", message_key)], limit=1
                )
                if existing:
                    return existing
        domain = [
            ("gateway_message_external_id", "=", dto.message_id),
            ("gateway_type", "=", gateway.gateway_type),
        ]
        if dto.instance:
            domain.append(("gateway_instance", "=", dto.instance))
        if dto.chat_id:
            domain.append(("gateway_chat_id", "=", dto.chat_id))
        return message_model.search(domain, limit=1)


    def _build_message_key(self, gateway, dto):
        """Stable key to dedupe message upserts across retries."""
        if not gateway or not dto:
            return False
        return self._build_message_key_from_values(
            gateway, dto.instance, dto.chat_id, dto.message_id
        )


    def _build_message_key_from_values(self, gateway, instance, chat_id, message_id):
        if not gateway:
            return False
        parts = [
            gateway.gateway_type or "",
            str(gateway.id or ""),
            instance or "",
            chat_id or "",
            message_id or "",
        ]
        return "|".join(parts)


    def _normalize_status(self, status_raw):
        status = (status_raw or "").strip().lower()
        if not status:
            return False
        compact = status.replace("_", "").replace(" ", "").replace("-", "")
        if compact in {"read", "readself", "seen"}:
            return "read"
        if compact in {"readack"}:
            return "read"
        if compact in {"delivered"}:
            return "delivered"
        if compact in {"deliveryack"}:
            return "delivered"
        if compact in {"sent"}:
            return "sent"
        if compact in {"serverack"}:
            return "sent"
        if compact in {"failed", "error", "exception", "canceled", "cancelled"}:
            return "failed"
        if compact in {"pending", "processing", "process"}:
            return "pending"
        return False


    def _status_rank(self, status):
        rank = {
            "pending": 1,
            "sent": 2,
            "delivered": 3,
            "read": 4,
            "failed": 99,
        }
        return rank.get(status or "", 0)


    def _should_update_status(self, current, incoming):
        if not incoming:
            return False
        if not current:
            return True
        return self._status_rank(incoming) >= self._status_rank(current)


    def _notification_status_rank(self, status):
        rank = {
            "ready": 0,
            "process": 0,
            "pending": 1,
            "sent": 2,
            "bounce": 98,
            "exception": 99,
            "canceled": -1,
        }
        return rank.get(status or "", 0)


    def _map_notification_status(self, normalized):
        if normalized == "pending":
            return "pending"
        if normalized in {"sent", "delivered", "read"}:
            return "sent"
        if normalized == "failed":
            return "exception"
        return False


    def _update_gateway_notification_status(
        self, gateway, message_id, normalized, status_raw
    ):
        notification_model = self.env["mail.notification"].sudo()
        if "gateway_message_id" not in notification_model._fields:
            return 0
        domain = [("gateway_message_id", "=", message_id)]
        if "gateway_type" in notification_model._fields and gateway:
            domain.append(("gateway_type", "=", gateway.gateway_type))
        notifications = notification_model.search(domain)
        if not notifications:
            return 0
        mapped_status = self._map_notification_status(normalized)
        updated = 0
        for notification in notifications:
            update_vals = {}
            if mapped_status:
                if self._notification_status_rank(mapped_status) >= self._notification_status_rank(
                    notification.notification_status
                ):
                    update_vals["notification_status"] = mapped_status
            if (
                normalized == "failed"
                and status_raw
                and "gateway_failure_reason" in notification._fields
            ):
                update_vals["gateway_failure_reason"] = status_raw
            read_updated = False
            if normalized == "read" and hasattr(notification, "_set_read_gateway"):
                notification._set_read_gateway()
                read_updated = True
            if update_vals:
                notification.write(update_vals)
                updated += 1
            elif read_updated:
                updated += 1
        return updated


    def _build_deleted_body(self, body):
        body_text = str(body or "")
        if not body_text:
            return Markup("<p><s>This message was deleted</s> <em>(mensagem apagada)</em></p>")
        if "<s>" in body_text or "<del>" in body_text:
            return body_text
        updated = re.sub(
            r"(<p[^>]*>)(.*?)(</p>)",
            lambda m: f"{m.group(1)}<s>{m.group(2)}</s> <em>(mensagem apagada)</em>{m.group(3)}",
            body_text,
            flags=re.DOTALL,
        )
        if updated != body_text:
            return Markup(updated)
        return Markup(f"<p><s>{body_text}</s> <em>(mensagem apagada)</em></p>")


    @staticmethod
    def _is_group_chat(chat_id):
        return str(chat_id or "").endswith("@g.us")

    @classmethod
    def _format_group_name(cls, chat_id):
        return f"Grupo {cls._format_chat_id(chat_id)}"

    @staticmethod
    def _format_chat_id(chat_id):
        chat_id = str(chat_id or "").strip()
        if "@" in chat_id:
            return chat_id.split("@", 1)[0]
        return chat_id
