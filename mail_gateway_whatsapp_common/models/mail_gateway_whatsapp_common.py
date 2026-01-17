import base64
import json
import logging
from datetime import datetime

import requests

from odoo import Command, fields, models
from odoo.tools import html_escape


class MailGatewayWhatsappCommon(models.AbstractModel):
    _name = "mail.gateway.whatsapp.common"
    _description = "WhatsApp Gateway Common"
    _abstract = True
    _logger = logging.getLogger(__name__)

    def _process_normalized(self, gateway, dto, channel, author=None):
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
        message_id = (dto.message_id or "").strip()
        chat_id = (dto.chat_id or "").strip()
        if not message_id:
            return {"status": "ignored", "reason": "missing_message_id"}
        if not chat_id:
            return {"status": "ignored", "reason": "missing_chat_id"}
        existing = self._find_existing_message(gateway, dto)
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
            }
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

        body = self._render_message_body(dto)
        if not body and not dto.has_attachments():
            return {"status": "ignored", "reason": "empty_body"}

        ctx = dict(self.env.context or {})
        ctx["no_gateway_notification"] = True
        post_channel = channel.with_context(**ctx)
        author_id = False
        if author._name == "mail.guest":
            public_user = self.env.ref("base.public_user", raise_if_not_found=False)
            if public_user:
                post_channel = post_channel.with_user(public_user.id)
            post_channel = post_channel.with_context(guest=author)
        else:
            author_id = author.id

        message = post_channel.sudo().message_post(
            body=body or None,
            author_id=author_id,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            gateway_type=gateway.gateway_type,
        )
        if not message:
            return {"status": "ignored", "reason": "message_not_created"}

        write_vals = {
            "gateway_message_external_id": message_id,
            "gateway_instance": dto.instance,
            "gateway_chat_id": chat_id,
            "gateway_sender_jid": dto.sender_jid,
            "gateway_sender_name": dto.sender_name,
            "gateway_from_me": bool(dto.from_me),
            "gateway_type": gateway.gateway_type,
        }
        webhook_log_id = self.env.context.get("gateway_webhook_log_id")
        if webhook_log_id and "gateway_webhook_log_id" in message._fields:
            write_vals["gateway_webhook_log_id"] = webhook_log_id
        if "gateway_payload_raw" in message._fields:
            try:
                write_vals["gateway_payload_raw"] = json.dumps(
                    dto.raw, ensure_ascii=True, sort_keys=True
                )
            except Exception:
                write_vals["gateway_payload_raw"] = str(dto.raw)
        message.sudo().write(write_vals)
        self._apply_message_timestamp(message, dto)

        return {
            "status": "ok",
            "message_id": message.id,
            "channel_id": channel.id,
        }

    def _ensure_guest_member(self, channel, author):
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

    def _apply_message_timestamp(self, message, dto):
        if not message or not dto or not dto.timestamp:
            return
        dt_value = self._normalize_timestamp(dto.timestamp)
        if not dt_value:
            return
        message.sudo().write({"date": dt_value, "write_date": dt_value})

    def _render_message_body(self, dto):
        text = (dto.text or "").strip()
        if not text:
            return ""
        if dto.text_is_html:
            return text
        return html_escape(text).replace("\n", "<br/>")

    def _normalize_timestamp(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return fields.Datetime.from_timestamp(value)
        if isinstance(value, str):
            return fields.Datetime.to_datetime(value)
        return False

    def _handle_contact_update(self, gateway, dto, channel, author=None):
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

    def _find_existing_message(self, gateway, dto):
        domain = [
            ("gateway_message_external_id", "=", dto.message_id),
            ("gateway_type", "=", gateway.gateway_type),
        ]
        if dto.instance:
            domain.append(("gateway_instance", "=", dto.instance))
        if dto.chat_id:
            domain.append(("gateway_chat_id", "=", dto.chat_id))
        return self.env["mail.message"].sudo().search(domain, limit=1)

    def _resolve_author(self, gateway, dto):
        if dto.from_me:
            user = gateway.webhook_user_id or self.env.user
            return user.partner_id if user else False
        return self._get_or_create_guest(gateway, dto)

    def _get_or_create_guest(self, gateway, dto):
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
        channel._broadcast(channel.channel_member_ids.mapped("partner_id").ids)
        return channel

    def _build_channel_members(self, gateway, author):
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
        chat_id = (dto.chat_id or "").strip()
        if not chat_id:
            return (dto.sender_name or "").strip()
        if self._is_group_chat(chat_id):
            return (dto.chat_name or "").strip() or self._format_group_name(chat_id)
        return (dto.sender_name or "").strip() or self._format_chat_id(chat_id)

    def _fetch_image_base64(self, url):
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
