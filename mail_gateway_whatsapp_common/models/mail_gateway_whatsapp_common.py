import base64
import json
import logging

import requests

from odoo import Command, models


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

        body = (dto.text or "").strip()
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

        return {
            "status": "ok",
            "message_id": message.id,
            "channel_id": channel.id,
        }

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
        guest_token = self._get_guest_token(dto)
        if not guest_token:
            return False
        guest_model = self.env["mail.guest"].sudo()
        guest = guest_model.search(
            [("gateway_id", "=", gateway.id), ("gateway_token", "=", guest_token)],
            limit=1,
        )
        name = self._get_guest_name(dto)
        if guest:
            if name and guest.name != name:
                guest.write({"name": name})
            return guest
        return guest_model.create(
            {
                "name": name,
                "gateway_id": gateway.id,
                "gateway_token": guest_token,
            }
        )

    def _get_guest_token(self, dto):
        if dto.is_group:
            return (dto.sender_participant_jid or dto.sender_jid or "").strip()
        return (dto.chat_id or "").strip()

    def _get_guest_name(self, dto):
        if dto.sender_name:
            return dto.sender_name
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
