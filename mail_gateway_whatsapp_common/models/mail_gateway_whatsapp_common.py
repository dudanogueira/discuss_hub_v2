import base64
import binascii
import json
import logging
import mimetypes
import re
from datetime import datetime

import requests
from markupsafe import Markup

from odoo import Command, fields, models
from odoo.tools import html_escape
from psycopg2 import IntegrityError


class MailGatewayWhatsappCommon(models.AbstractModel):
    """Shared webhook processing for WhatsApp gateway providers.

    Providers normalize raw payloads into a DTO and call `_process_normalized`,
    which handles idempotency, guest resolution, channel creation, and posting.
    """

    _name = "mail.gateway.whatsapp.common"
    _description = "WhatsApp Gateway Common"
    _abstract = True
    _logger = logging.getLogger(__name__)
    _br_tag_re = re.compile(r"<br\s*/?>", re.IGNORECASE)

    def _process_normalized(self, gateway, dto, channel, author=None):
        """Dispatch a normalized event to the matching handler."""
        if not gateway or not dto or not dto.event:
            return {
                "status": "ignored",
                "reason": "missing_gateway_or_event",
            }
        handler_name = f"_handle_{dto.event.replace('.', '_')}"
        handler = getattr(self, handler_name, None)
        if not handler:
            return {
                "status": "ignored",
                "reason": "unsupported_event",
                "event": dto.event,
            }
        return handler(gateway, dto, channel, author=author)

    def _handle_message_upsert(self, gateway, dto, channel, author=None):
        """Create or update a message coming from the gateway."""
        message_id = (dto.message_id or "").strip()
        chat_id = (dto.chat_id or "").strip()
        if not message_id:
            return {"status": "ignored", "reason": "missing_message_id"}
        if not chat_id:
            return {"status": "ignored", "reason": "missing_chat_id"}
        message_key = self._build_message_key(gateway, dto)
        existing = self._find_existing_message(gateway, dto, message_key=message_key)
        if existing:
            update_vals = {}
            webhook_log_id = self.env.context.get("gateway_webhook_log_id")
            if (
                webhook_log_id
                and "gateway_webhook_log_id" in existing._fields
                and not existing.gateway_webhook_log_id
            ):
                update_vals["gateway_webhook_log_id"] = webhook_log_id
            if "gateway_payload_raw" in existing._fields and not existing.gateway_payload_raw:
                try:
                    update_vals["gateway_payload_raw"] = json.dumps(
                        dto.raw, ensure_ascii=True, sort_keys=True
                    )
                except Exception:
                    update_vals["gateway_payload_raw"] = str(dto.raw)
            backfill_values = {
                "gateway_message_external_id": message_id,
                "gateway_instance": dto.instance,
                "gateway_chat_id": chat_id,
                "gateway_sender_jid": dto.sender_jid,
                "gateway_sender_name": dto.sender_name,
                "gateway_from_me": bool(dto.from_me),
                "gateway_type": gateway.gateway_type,
                "gateway_message_key": message_key,
                "gateway_quote_external_id": (dto.quote_id or "").strip() or False,
                "gateway_quote_text": dto.quote_text,
            }
            # Backfill metadata only when missing to keep idempotent updates cheap.
            for field_name, value in backfill_values.items():
                if field_name not in existing._fields:
                    continue
                if getattr(existing, field_name):
                    continue
                if value in (None, "", False):
                    continue
                update_vals[field_name] = value
            if update_vals:
                existing.sudo().write(update_vals)
            return {
                "status": "duplicate",
                "message_id": existing.id,
            }

        author = author or self._resolve_author(gateway, dto)
        if not author:
            return {"status": "ignored", "reason": "author_not_found"}

        channel = channel or self._get_or_create_channel(gateway, dto, author)
        if not channel:
            return {"status": "ignored", "reason": "channel_not_found"}
        self._apply_channel_metadata(channel, dto)
        self._ensure_guest_member(channel, author)

        attachments = self._prepare_attachments(dto)
        body = self._render_message_body(dto)
        if not body and not attachments:
            return {"status": "ignored", "reason": "empty_body"}
        parent_message = self._find_quoted_message(gateway, dto)

        ctx = dict(self.env.context or {})
        ctx["no_gateway_notification"] = True
        post_channel = channel.with_context(**ctx)
        author_id = False
        if author._name == "mail.guest":
            # Post as public user with guest context so it renders as the guest.
            public_user = self.env.ref("base.public_user", raise_if_not_found=False)
            if public_user:
                post_channel = post_channel.with_user(public_user.id)
            post_channel = post_channel.with_context(guest=author)
        else:
            author_id = author.id

        msg_kwargs = {
            "gateway_message_external_id": message_id,
            "gateway_instance": dto.instance,
            "gateway_chat_id": chat_id,
            "gateway_sender_jid": dto.sender_jid,
            "gateway_sender_name": dto.sender_name,
            "gateway_from_me": bool(dto.from_me),
            "gateway_type": gateway.gateway_type,
            "gateway_message_key": message_key,
            "gateway_quote_external_id": (dto.quote_id or "").strip() or False,
            "gateway_quote_text": dto.quote_text,
        }
        webhook_log_id = self.env.context.get("gateway_webhook_log_id")
        if webhook_log_id and "gateway_webhook_log_id" in self.env["mail.message"]._fields:
            msg_kwargs["gateway_webhook_log_id"] = webhook_log_id
        if "gateway_payload_raw" in self.env["mail.message"]._fields:
            try:
                msg_kwargs["gateway_payload_raw"] = json.dumps(
                    dto.raw, ensure_ascii=True, sort_keys=True
                )
            except Exception:
                msg_kwargs["gateway_payload_raw"] = str(dto.raw)
        try:
            with self.env.cr.savepoint():
                message = post_channel.sudo().message_post(
                    body=body or "",
                    body_is_html=True,
                    author_id=author_id,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                    parent_id=parent_message.id if parent_message else False,
                    attachments=attachments or None,
                )
        except IntegrityError:
            existing = self._find_existing_message(gateway, dto)
            if existing:
                return {"status": "duplicate", "message_id": existing.id}
            raise
        if not message:
            return {"status": "ignored", "reason": "message_not_created"}

        # Store gateway metadata after message creation to preserve mail.thread flow.
        message.sudo().write(msg_kwargs)
        self._apply_message_timestamp(message, dto)

        return {
            "status": "ok",
            "message_id": message.id,
            "channel_id": channel.id,
        }

    def _handle_reaction_upsert(self, gateway, dto, channel, author=None):
        """Create or update reactions on an existing message."""
        target_id = (dto.reaction_target_id or dto.message_id or "").strip()
        reaction = (dto.reaction or "").strip()
        if not target_id:
            return {"status": "ignored", "reason": "missing_reaction_target"}
        if not reaction:
            return {"status": "ignored", "reason": "missing_reaction"}

        message = self._find_message_by_external_id(
            gateway,
            target_id,
            chat_id=dto.chat_id,
            instance=dto.instance,
        )
        if not message:
            return {"status": "ignored", "reason": "message_not_found"}

        author = author or self._resolve_author(gateway, dto)
        if not author:
            return {"status": "ignored", "reason": "author_not_found"}

        reaction_model = self.env["mail.message.reaction"].sudo()
        domain = [("message_id", "=", message.id), ("content", "=", reaction)]
        if author._name == "mail.guest":
            domain.append(("guest_id", "=", author.id))
        else:
            domain.append(("partner_id", "=", author.id))
        existing = reaction_model.search(domain, limit=1)
        if existing:
            return {"status": "duplicate", "reaction_id": existing.id, "message_id": message.id}

        vals = {"message_id": message.id, "content": reaction}
        if author._name == "mail.guest":
            vals["guest_id"] = author.id
        else:
            vals["partner_id"] = author.id
        try:
            with self.env.cr.savepoint():
                new_reaction = reaction_model.create(vals)
        except IntegrityError:
            existing = reaction_model.search(domain, limit=1)
            if existing:
                return {"status": "duplicate", "reaction_id": existing.id, "message_id": message.id}
            raise

        return {"status": "ok", "reaction_id": new_reaction.id, "message_id": message.id}

    def _handle_reaction_delete(self, gateway, dto, channel, author=None):
        """Remove reactions from an existing message."""
        target_id = (dto.reaction_target_id or dto.message_id or "").strip()
        if not target_id:
            return {"status": "ignored", "reason": "missing_reaction_target"}

        message = self._find_message_by_external_id(
            gateway,
            target_id,
            chat_id=dto.chat_id,
            instance=dto.instance,
        )
        if not message:
            return {"status": "ignored", "reason": "message_not_found"}

        author = author or self._resolve_author(gateway, dto)
        if not author:
            return {"status": "ignored", "reason": "author_not_found"}

        reaction_model = self.env["mail.message.reaction"].sudo()
        domain = [("message_id", "=", message.id)]
        if author._name == "mail.guest":
            domain.append(("guest_id", "=", author.id))
        else:
            domain.append(("partner_id", "=", author.id))
        reaction = (dto.reaction or "").strip()
        if reaction:
            domain.append(("content", "=", reaction))

        reactions = reaction_model.search(domain)
        if not reactions:
            return {"status": "ignored", "reason": "reaction_not_found"}
        count = len(reactions)
        reactions.unlink()
        return {"status": "ok", "message_id": message.id, "deleted": count}

    def _handle_message_status(self, gateway, dto, channel, author=None):
        """Update delivery/read status for a gateway message."""
        message_id = (dto.message_id or "").strip()
        if not message_id:
            return {"status": "ignored", "reason": "missing_message_id"}
        status_raw = (dto.status_raw or dto.status or "").strip()
        normalized = self._normalize_status(status_raw)

        updated_message = False
        message = self._find_message_by_external_id(
            gateway,
            message_id,
            chat_id=dto.chat_id,
            instance=dto.instance,
        )
        if message:
            update_vals = {}
            if (
                status_raw
                and "gateway_message_status_raw" in message._fields
                and message.gateway_message_status_raw != status_raw
            ):
                update_vals["gateway_message_status_raw"] = status_raw
            if normalized and "gateway_message_status" in message._fields:
                if self._should_update_status(message.gateway_message_status, normalized):
                    update_vals["gateway_message_status"] = normalized
            if update_vals:
                message.sudo().write(update_vals)
                updated_message = True

        updated_notifications = self._update_gateway_notification_status(
            gateway, message_id, normalized, status_raw
        )
        if updated_message or updated_notifications:
            return {
                "status": "ok",
                "message_id": message.id if message else False,
                "notification_count": updated_notifications,
            }
        return {"status": "ignored", "reason": "message_not_found"}

    def _handle_message_delete(self, gateway, dto, channel, author=None):
        """Mark a gateway message as deleted without removing it."""
        message_id = (dto.message_id or "").strip()
        if not message_id:
            return {"status": "ignored", "reason": "missing_message_id"}

        message = self._find_message_by_external_id(
            gateway,
            message_id,
            chat_id=dto.chat_id,
            instance=dto.instance,
        )
        if not message:
            return {"status": "ignored", "reason": "message_not_found"}
        if "gateway_is_deleted" in message._fields and message.gateway_is_deleted:
            return {"status": "duplicate", "message_id": message.id}

        updated_body = self._build_deleted_body(message.body)
        update_vals = {"body": updated_body}
        if "gateway_is_deleted" in message._fields:
            update_vals["gateway_is_deleted"] = True
        if "gateway_deleted_at" in message._fields:
            update_vals["gateway_deleted_at"] = fields.Datetime.now()
        message.sudo().write(update_vals)
        return {"status": "ok", "message_id": message.id}

    def _ensure_guest_member(self, channel, author):
        """Ensure a guest author is a member of the channel."""
        if not channel or not author or author._name != "mail.guest":
            return
        member_model = self.env["discuss.channel.member"].sudo()
        if "guest_id" not in member_model._fields:
            return
        existing = member_model.search(
            [("channel_id", "=", channel.id), ("guest_id", "=", author.id)], limit=1
        )
        if existing:
            return
        member_model.create({"channel_id": channel.id, "guest_id": author.id, "unpin_dt": False})

    def _find_quoted_message(self, gateway, dto):
        quote_id = (dto.quote_id or "").strip()
        if not quote_id:
            return False
        message = self._find_message_by_external_id(
            gateway,
            quote_id,
            chat_id=dto.chat_id,
            instance=dto.instance,
        )
        if message:
            return message
        if dto.chat_id:
            return self._find_message_by_external_id(
                gateway,
                quote_id,
                chat_id=None,
                instance=dto.instance,
            )
        return False

    def _prepare_attachments(self, dto):
        attachments = []
        for attachment in dto.attachments or []:
            if not isinstance(attachment, dict):
                continue
            payload = attachment.get("datas")
            if not payload:
                continue
            decoded = self._decode_attachment_payload(payload)
            if not decoded:
                continue
            mimetype = (attachment.get("mimetype") or "").strip()
            name = self._normalize_attachment_name(
                attachment.get("name"), mimetype, dto
            )
            info = {}
            is_voice = bool(mimetype.startswith("audio/"))
            if not is_voice and dto.message_type:
                is_voice = "audio" in (dto.message_type or "").lower()
            if is_voice:
                info["voice"] = True
            if info:
                attachments.append((name, decoded, info))
            else:
                attachments.append((name, decoded))
        return attachments

    def _decode_attachment_payload(self, payload):
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, bytearray):
            return bytes(payload)
        if isinstance(payload, str):
            payload = payload.strip()
            if not payload:
                return False
            if "base64," in payload:
                payload = payload.split("base64,", 1)[1]
            try:
                return base64.b64decode(payload)
            except (binascii.Error, ValueError):
                return payload.encode("utf-8")
        return False

    def _normalize_attachment_name(self, name, mimetype, dto):
        filename = (name or "").strip()
        if not filename:
            filename = (dto.message_id or "").strip() or "attachment"
        extension = self._guess_attachment_extension(mimetype)
        if extension and "." not in filename:
            filename = f"{filename}{extension}"
        return filename

    def _guess_attachment_extension(self, mimetype):
        if not mimetype:
            return ".bin"
        extension = mimetypes.guess_extension(mimetype)
        return extension or ".bin"

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

    def _handle_contact_update(self, gateway, dto, channel, author=None):
        """Sync guest details and optional avatar based on contact updates."""
        contact_jid = (dto.contact_jid or dto.chat_id or "").strip()
        if not contact_jid:
            return {"status": "ignored", "reason": "missing_contact_jid"}
        if dto.is_group:
            return {"status": "ignored", "reason": "group_contact_ignored"}
        if not dto.chat_id:
            dto.chat_id = contact_jid
        guest = self._find_guest_by_tokens(gateway, dto)
        if not guest:
            if not dto.contact_name:
                return {"status": "ignored", "reason": "guest_not_found"}
            guest = self._get_or_create_guest(gateway, dto)
        if not guest:
            return {"status": "ignored", "reason": "guest_not_found"}
        update_vals = {}
        if (
            dto.contact_profile_pic_url
            and "gateway_profile_pic_url" in guest._fields
            and guest.gateway_profile_pic_url != dto.contact_profile_pic_url
        ):
            update_vals["gateway_profile_pic_url"] = dto.contact_profile_pic_url
        if update_vals:
            guest.sudo().write(update_vals)
        if dto.contact_profile_pic_url:
            channel_id = gateway._get_channel_id(contact_jid)
            if channel_id:
                channel = self.env["discuss.channel"].browse(channel_id)
                if channel and not channel.image_128:
                    image_base64 = self._fetch_image_base64(dto.contact_profile_pic_url)
                    if image_base64:
                        channel.sudo().write({"image_128": image_base64})
        return {"status": "ok", "guest_id": guest.id}

    def _handle_chat_update(self, gateway, dto, channel, author=None):
        """Update channel metadata such as name and unread count."""
        chat_id = (dto.chat_id or "").strip()
        if not chat_id:
            return {"status": "ignored", "reason": "missing_chat_id"}
        channel_id = gateway._get_channel_id(chat_id)
        if not channel_id:
            return {"status": "ignored", "reason": "channel_not_found"}
        channel = self.env["discuss.channel"].browse(channel_id)
        update_vals = {}
        if dto.chat_name and self._should_update_channel_name(channel, dto, chat_id):
            update_vals["name"] = dto.chat_name.strip()
        if (
            dto.chat_unread_count is not None
            and "gateway_unread_count" in channel._fields
            and channel.gateway_unread_count != dto.chat_unread_count
        ):
            update_vals["gateway_unread_count"] = dto.chat_unread_count
        if update_vals:
            channel.sudo().write(update_vals)
        return {"status": "ok", "channel_id": channel.id}

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
        compact = status.replace("_", "").replace(" ", "")
        if compact in {"read", "readself", "seen"}:
            return "read"
        if compact in {"delivered"}:
            return "delivered"
        if compact in {"sent"}:
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
            return Markup("<p><s>This message was deleted</s></p>")
        if "<s>" in body_text or "<del>" in body_text:
            return body_text
        updated = re.sub(
            r"(<p[^>]*>)(.*?)(</p>)",
            lambda m: f"{m.group(1)}<s>{m.group(2)}</s>{m.group(3)}",
            body_text,
            flags=re.DOTALL,
        )
        if updated != body_text:
            return Markup(updated)
        return Markup(f"<p><s>{body_text}</s></p>")

    def _resolve_author(self, gateway, dto):
        """Resolve the author as a partner (outbound) or guest (inbound)."""
        if dto.from_me:
            user = gateway.webhook_user_id or self.env.user
            return user.partner_id if user else False
        return self._get_or_create_guest(gateway, dto)

    def _get_or_create_guest(self, gateway, dto):
        """Find or create a mail.guest using gateway identifiers."""
        token_candidates = self._get_guest_token_candidates(dto)
        if not token_candidates:
            return False
        primary_token = token_candidates[0]
        guest_model = self.env["mail.guest"].sudo()
        guest = self._find_guest_by_tokens(gateway, dto, token_candidates)
        if guest and guest.gateway_token != primary_token:
            guest.write({"gateway_token": primary_token})
        name = self._get_guest_name(dto)
        if guest:
            if name and guest.name != name:
                guest.write({"name": name})
            return guest
        return guest_model.create(
            {
                "name": name,
                "gateway_id": gateway.id,
                "gateway_token": primary_token,
            }
        )

    def _find_guest_by_tokens(self, gateway, dto, tokens=None):
        token_candidates = tokens or self._get_guest_token_candidates(dto)
        if not token_candidates:
            return False
        guest_model = self.env["mail.guest"].sudo()
        return guest_model.search(
            [("gateway_id", "=", gateway.id), ("gateway_token", "in", token_candidates)],
            limit=1,
        )

    def _get_guest_token_candidates(self, dto):
        if dto.is_group:
            candidates = [
                (dto.sender_jid_alt or "").strip(),
                (dto.sender_participant_jid or "").strip(),
                (dto.sender_jid or "").strip(),
            ]
            return [token for token in candidates if token]
        if dto.contact_jid:
            return [(dto.contact_jid or "").strip()]
        if dto.chat_id:
            return [(dto.chat_id or "").strip()]
        return []

    def _get_guest_name(self, dto):
        if dto.sender_name:
            return dto.sender_name
        if dto.contact_name:
            return dto.contact_name
        if dto.is_group:
            return self._format_chat_id(dto.sender_participant_jid or dto.sender_jid)
        return self._format_chat_id(dto.chat_id)

    def _get_or_create_channel(self, gateway, dto, author):
        """Find or create the gateway channel for a chat_id."""
        chat_id = (dto.chat_id or "").strip()
        if not chat_id:
            return False
        channel_id = gateway._get_channel_id(chat_id)
        if channel_id:
            return self.env["discuss.channel"].browse(channel_id)
        channel_name = self._get_channel_name(dto)
        members = self._build_channel_members(gateway, author)
        channel_env = self.env["discuss.channel"].sudo()
        channel_env = channel_env.with_user(gateway.webhook_user_id or self.env.user)
        channel_env = channel_env.with_context(install_mode=True)
        try:
            channel = channel_env.create(
                {
                    "name": channel_name,
                    "channel_type": "gateway",
                    "gateway_id": gateway.id,
                    "gateway_channel_token": chat_id,
                    "channel_member_ids": members,
                    "company_id": gateway.company_id.id,
                    "description": (dto.chat_description or "").strip() or False,
                }
            )
        except IntegrityError:
            # Another transaction created the same gateway channel concurrently.
            self.env.cr.rollback()
            channel_id = gateway._get_channel_id(chat_id)
            if not channel_id:
                raise
            channel = self.env["discuss.channel"].browse(channel_id)
        channel._broadcast(channel.channel_member_ids.mapped("partner_id").ids)
        return channel

    def _build_channel_members(self, gateway, author):
        """Add gateway members and the author to the channel."""
        members = []
        for user in gateway.member_ids:
            if user.partner_id:
                members.append(
                    Command.create(
                        {
                            "partner_id": user.partner_id.id,
                            "unpin_dt": False,
                        }
                    )
                )
        if author and author._name == "res.partner":
            members.append(
                Command.create({"partner_id": author.id, "unpin_dt": False})
            )
        elif author and author._name == "mail.guest":
            member_model = self.env["discuss.channel.member"]
            if "guest_id" in member_model._fields:
                members.append(
                    Command.create({"guest_id": author.id, "unpin_dt": False})
                )
        return members

    def _apply_channel_metadata(self, channel, dto):
        """Update group channel metadata when missing or clearly outdated."""
        chat_id = (dto.chat_id or "").strip()
        if not chat_id or not self._is_group_chat(chat_id):
            return
        update_vals = {}
        if dto.chat_name:
            if self._should_update_channel_name(channel, dto, chat_id):
                update_vals["name"] = dto.chat_name.strip()
        if dto.chat_description and not channel.description:
            update_vals["description"] = dto.chat_description.strip()
        if dto.chat_picture_url and not channel.image_128:
            image_base64 = self._fetch_image_base64(dto.chat_picture_url)
            if image_base64:
                update_vals["image_128"] = image_base64
        if update_vals:
            channel.sudo().write(update_vals)

    def _should_update_channel_name(self, channel, dto, chat_id):
        """Heuristic to replace fallback names with a better one."""
        current_name = (channel.name or "").strip()
        if not current_name:
            return True
        new_name = (dto.chat_name or "").strip()
        if not new_name or current_name == new_name:
            return False
        fallback_group = self._format_group_name(chat_id)
        fallback_chat = self._format_chat_id(chat_id)
        sender_name = (dto.sender_name or "").strip()
        if current_name in {fallback_group, fallback_chat}:
            return True
        if sender_name and current_name == sender_name:
            return True
        return False

    def _get_channel_name(self, dto):
        """Compute a human-friendly channel name."""
        chat_id = (dto.chat_id or "").strip()
        if not chat_id:
            return (dto.sender_name or "").strip()
        if self._is_group_chat(chat_id):
            return (dto.chat_name or "").strip() or self._format_group_name(chat_id)
        if dto.from_me:
            if dto.contact_name:
                return dto.contact_name.strip()
            return self._format_chat_id(chat_id)
        return (dto.sender_name or "").strip() or self._format_chat_id(chat_id)

    def _fetch_image_base64(self, url):
        """Download and convert images to base64 for channel avatars."""
        if not url:
            return False
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200 or not response.content:
                return False
            return base64.b64encode(response.content).decode("ascii")
        except Exception as exc:
            self._logger.warning("Failed to fetch group image: %s", exc)
            return False

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
