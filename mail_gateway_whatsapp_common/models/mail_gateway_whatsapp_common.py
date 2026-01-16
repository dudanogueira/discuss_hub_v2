# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Servico comum para processar payloads normalizados de WhatsApp."""

import base64
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MailGatewayWhatsappCommon(models.AbstractModel):
    _name = "mail.gateway.whatsapp.common"
    _description = "Servico comum para gateways WhatsApp nao-oficiais"

    _CANONICAL_EVENTS = {
        "message_upsert",
        "message_status",
        "message_delete",
        "reaction_upsert",
        "reaction_delete",
    }
    _EVENT_ALIASES = {
        "messages.upsert": "message_upsert",
        "message.upsert": "message_upsert",
        "messages_upsert": "message_upsert",
        "message": "message_upsert",
        "send.message": "message_upsert",
        "send_message": "message_upsert",
        "messages.update": "message_status",
        "message.update": "message_status",
        "message.status": "message_status",
        "message_status": "message_status",
        "status": "message_status",
        "messages.delete": "message_delete",
        "message.delete": "message_delete",
        "message_delete": "message_delete",
        "delete": "message_delete",
        "reaction": "reaction_upsert",
        "reaction.upsert": "reaction_upsert",
        "reaction_upsert": "reaction_upsert",
        "reaction.delete": "reaction_delete",
        "reaction_delete": "reaction_delete",
        "reaction.remove": "reaction_delete",
        "reaction_remove": "reaction_delete",
    }

    def _process_normalized(self, gateway, dto, channel, author=None):
        """Processa um NormalizedPayload e cria/atualiza mail.message.

        Parametros:
        - gateway: registro de mail.gateway
        - dto: NormalizedPayload
        - channel: opcional; se None, o common resolve/cria o canal
        - author: opcional (res.partner ou mail.guest)
        """

        event = self._normalize_event(dto)
        if not event:
            _logger.warning("WhatsApp common: unknown event %s", dto.event)
            return False
        if not self._validate_dto(dto, event):
            return False

        channel_needed = event == "message_upsert"
        if channel_needed:
            if not channel:
                channel = self._get_or_create_channel(gateway, dto)
            if not channel:
                return False

        author_needed = event in {"message_upsert", "reaction_upsert", "reaction_delete"}
        if author is None and author_needed:
            author = self._resolve_author(gateway, dto)
        if channel:
            channel = self._prepare_channel_for_author(channel, author)

        if event == "message_upsert":
            return self._handle_message_upsert(gateway, dto, channel, author)
        if event == "message_status":
            return self._handle_message_status(gateway, dto)
        if event == "message_delete":
            return self._handle_message_delete(gateway, dto)
        if event == "reaction_upsert":
            return self._handle_reaction_upsert(gateway, dto, author)
        if event == "reaction_delete":
            return self._handle_reaction_delete(gateway, dto, author)
        # Eventos desconhecidos: ignora silenciosamente
        return False

    # Channel resolution -----------------------------------------------------
    def _get_or_create_channel(self, gateway, dto):
        token = self._get_channel_token(dto)
        if not token:
            _logger.warning("WhatsApp common: missing chat token in DTO")
            return False
        Channel = self.env["discuss.channel"].sudo()
        domain = [
            ("channel_type", "=", "gateway"),
            ("gateway_id", "=", gateway.id),
            ("gateway_channel_token", "=", token),
        ]
        channel = Channel.search(domain, limit=1)
        if channel:
            self._refresh_channel_name(channel, dto, token)
            return channel
        vals = {
            "name": self._get_channel_name(dto, token),
            "channel_type": "gateway",
            "gateway_id": gateway.id,
            "gateway_channel_token": token,
        }
        return Channel.create(vals)

    def _get_channel_token(self, dto):
        for token in (
            dto.chat_id,
            dto.sender_jid,
            dto.sender_jid_alt,
            dto.sender_participant_jid,
        ):
            if token:
                return token
        return False

    def _get_channel_name(self, dto, token):
        name = (dto.sender_name or "").strip()
        return name or token

    def _refresh_channel_name(self, channel, dto, token):
        desired = self._get_channel_name(dto, token)
        if desired and channel.name != desired:
            channel.sudo().write({"name": desired})

    # DTO validation ---------------------------------------------------------
    def _normalize_event(self, dto):
        raw = (dto.event or "").strip().lower()
        if not raw:
            return False
        raw = raw.replace(" ", "_").replace("-", "_").replace("/", ".")
        dotted = raw.replace("_", ".")
        underscored = raw.replace(".", "_")
        for key in (raw, dotted, underscored):
            mapped = self._EVENT_ALIASES.get(key)
            if mapped:
                return mapped
        if underscored in self._CANONICAL_EVENTS:
            return underscored
        return False

    def _validate_dto(self, dto, event):
        missing = []
        if event == "message_upsert":
            if not dto.message_id:
                missing.append("message_id")
            if not self._get_channel_token(dto):
                missing.append("chat_id_or_sender_jid")
        elif event == "message_status":
            if not dto.message_id:
                missing.append("message_id")
            if not (dto.status or dto.status_raw):
                missing.append("status")
        elif event == "message_delete":
            if not dto.message_id:
                missing.append("message_id")
        elif event == "reaction_upsert":
            if not dto.reaction_target_id:
                missing.append("reaction_target_id")
            if not dto.reaction:
                missing.append("reaction")
        elif event == "reaction_delete":
            if not dto.reaction_target_id:
                missing.append("reaction_target_id")
        if missing:
            _logger.warning(
                "WhatsApp common: invalid DTO for %s, missing: %s",
                event,
                ", ".join(missing),
            )
            return False
        return True

    # Author resolution ------------------------------------------------------
    def _resolve_author(self, gateway, dto):
        if dto.from_me:
            return gateway.webhook_user_id.partner_id

        sender_jid = dto.sender_jid or dto.chat_id
        if not sender_jid:
            return gateway.webhook_user_id.partner_id

        guest = (
            self.env["mail.guest"]
            .sudo()
            .search(
                [
                    ("gateway_id", "=", gateway.id),
                    ("gateway_token", "=", str(sender_jid)),
                ],
                limit=1,
            )
        )
        vals = self._guest_values(gateway, dto, sender_jid)
        if guest:
            guest.sudo().write(vals)
            return guest
        return self.env["mail.guest"].sudo().create(vals)

    def _prepare_channel_for_author(self, channel, author):
        if author and author._name == "mail.guest":
            public_user = self.env.ref("base.public_user")
            return channel.with_user(public_user.id).with_context(guest=author)
        return channel

    def _guest_values(self, gateway, dto, sender_jid):
        push_name = (dto.sender_name or "").strip()
        values = {
            "name": push_name or sender_jid,
            "gateway_id": gateway.id,
            "gateway_token": sender_jid,
            "last_push_name": push_name or False,
            "whatsapp_remote_jid": dto.sender_jid or sender_jid,
            "whatsapp_remote_jid_alt": dto.sender_jid_alt,
            "whatsapp_participant_jid": dto.sender_participant_jid,
        }
        number = self._extract_whatsapp_number(dto.sender_jid or sender_jid)
        if number:
            values["whatsapp_number"] = number
        return values

    def _extract_whatsapp_number(self, jid):
        if not jid or not isinstance(jid, str):
            return False
        if "@g.us" in jid:
            return False
        number = jid.split("@", 1)[0]
        return number or False

    # Handlers ---------------------------------------------------------------
    def _handle_message_upsert(self, gateway, dto, channel, author):
        msg = self._find_message(gateway, dto.message_id)
        body = dto.text or dto.caption or ""
        if dto.media_url and not dto.media_b64:
            body = body or ""
            if dto.media_url not in body:
                body = (body + "\n" if body else "") + dto.media_url
        attachments = self._prepare_attachments(dto)
        mapped_status = self._map_status(dto.status)
        values = {
            "gateway_id": gateway.id,
            "gateway_provider": dto.provider,
            "gateway_instance": dto.instance,
            "gateway_remote_id": dto.message_id,
            "gateway_chat_id": dto.chat_id,
            "gateway_status": mapped_status,
            "gateway_status_raw": dto.status_raw or dto.status,
            "gateway_quoted_remote_id": dto.quote_id,
            "gateway_has_reaction": dto.has_reaction(),
        }
        if dto.raw and "gateway_payload_raw" in self.env["mail.message"]._fields:
            values["gateway_payload_raw"] = self._safe_json(dto.raw)

        parent_id = False
        if dto.quote_id:
            quoted = self._find_message(gateway, dto.quote_id)
            if quoted:
                parent_id = quoted.id

        if msg:
            update_vals = {
                "body": body or msg.body,
                "gateway_status": self._progress_status(msg.gateway_status, mapped_status),
                "gateway_status_raw": dto.status_raw or dto.status or msg.gateway_status_raw,
                "gateway_has_reaction": msg.gateway_has_reaction or dto.has_reaction(),
                "gateway_quoted_remote_id": dto.quote_id or msg.gateway_quoted_remote_id,
            }
            if parent_id and not msg.parent_id:
                update_vals["parent_id"] = parent_id
            msg.sudo().write({k: v for k, v in update_vals.items() if v is not None})
        else:
            msg = (
                channel.sudo()
                .with_context(
                    no_gateway_notification=True,
                )
                .message_post(
                    body=body or False,
                    author_id=author.id if author and author._name == "res.partner" else False,
                    subtype_xmlid="mail.mt_comment",
                    attachments=attachments,
                    parent_id=parent_id,
                    message_type="comment",
                )
            )
            msg.sudo().write(values)
        return msg

    def _handle_message_status(self, gateway, dto):
        msg = self._find_message(gateway, dto.message_id)
        if not msg:
            return False
        mapped_status = self._map_status(dto.status)
        new_status = self._progress_status(msg.gateway_status, mapped_status)
        updates = {
            "gateway_status": new_status,
            "gateway_status_raw": dto.status_raw or dto.status or msg.gateway_status_raw,
        }
        msg.sudo().write({k: v for k, v in updates.items() if v is not None})
        return msg

    def _handle_message_delete(self, gateway, dto):
        msg = self._find_message(gateway, dto.message_id)
        if not msg:
            return False
        msg.sudo().write({"gateway_deleted": True, "gateway_status": "deleted"})
        return msg

    def _handle_reaction_upsert(self, gateway, dto, author):
        target = self._find_message(gateway, dto.reaction_target_id)
        if not target or not dto.reaction:
            return False
        if not author:
            return False
        domain = [("message_id", "=", target.id), ("reaction", "=", dto.reaction)]
        if author._name == "res.partner":
            domain.append(("partner_id", "=", author.id))
        else:
            domain.append(("guest_id", "=", author.id))
        reaction = self.env["mail.message.reaction"].sudo().search(domain, limit=1)
        vals = {"reaction": dto.reaction, "message_id": target.id}
        if author._name == "res.partner":
            vals["partner_id"] = author.id
        else:
            vals["guest_id"] = author.id
        if reaction:
            reaction.write(vals)
        else:
            self.env["mail.message.reaction"].sudo().create(vals)
        target.sudo().write({"gateway_has_reaction": True})
        return target

    def _handle_reaction_delete(self, gateway, dto, author):
        target = self._find_message(gateway, dto.reaction_target_id)
        if not target:
            return False
        if not author:
            return False
        domain = [("message_id", "=", target.id)]
        if author._name == "res.partner":
            domain.append(("partner_id", "=", author.id))
        else:
            domain.append(("guest_id", "=", author.id))
        reactions = self.env["mail.message.reaction"].sudo().search(domain)
        if reactions:
            reactions.unlink()
        remaining = (
            self.env["mail.message.reaction"].sudo().search_count([("message_id", "=", target.id)])
            > 0
        )
        target.sudo().write({"gateway_has_reaction": remaining})
        return target

    # Helpers ---------------------------------------------------------------
    def _find_message(self, gateway, remote_id):
        if not remote_id:
            return False
        return (
            self.env["mail.message"]
            .sudo()
            .search(
                [("gateway_id", "=", gateway.id), ("gateway_remote_id", "=", remote_id)],
                limit=1,
            )
        )

    def _progress_status(self, current, new):
        if not new:
            return current
        order = ["sent", "delivered", "read"]
        if new not in order:
            return new
        if current not in order:
            return new
        return order[max(order.index(current), order.index(new))]

    def _map_status(self, status):
        if not status:
            return False
        status_upper = str(status).upper()
        mapping = {
            "MESSAGE_SENT": "sent",
            "SENT": "sent",
            "SERVER_ACK": "sent",
            "DELIVERY_ACK": "delivered",
            "DELIVERED": "delivered",
            "MESSAGE_DELIVERED": "delivered",
            "READ": "read",
            "READ_ACK": "read",
            "MESSAGE_READ": "read",
        }
        return mapping.get(status_upper, False)

    def _prepare_attachments(self, dto):
        """Return attachments for `message_post(attachments=...)`.

        Odoo expects a list of tuples `(name, content_bytes)` or
        `(name, content_bytes, info_dict)`, where content is NOT base64 encoded.
        """

        attachments = []
        for att in dto.attachments:
            name = att.get("name") or att.get("filename") or "attachment"
            mimetype = att.get("mimetype") or att.get("mime")
            datas_b64 = att.get("datas") or att.get("data") or att.get("media_b64")
            content = self._b64_to_bytes(datas_b64)
            if not content:
                continue
            info = {}
            if mimetype:
                info["mimetype"] = mimetype
            attachments.append((name, content, info) if info else (name, content))

        if dto.media_b64:
            content = self._b64_to_bytes(dto.media_b64)
            if content:
                info = {}
                if dto.mime:
                    info["mimetype"] = dto.mime
                name = dto.filename or "attachment"
                attachments.append((name, content, info) if info else (name, content))

        return attachments

    def _b64_to_bytes(self, value):
        if not value:
            return False
        if isinstance(value, (bytes, bytearray)):
            try:
                return base64.b64decode(value)
            except Exception:
                return bytes(value)
        if not isinstance(value, str):
            return False

        payload = value.strip()
        if payload.startswith("data:") and "," in payload:
            payload = payload.split(",", 1)[1].strip()
        try:
            return base64.b64decode(payload)
        except Exception:
            _logger.debug("Unable to decode base64 attachment payload")
            return False

    def _safe_json(self, payload):
        try:
            import json

            return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        except Exception:  # pragma: no cover
            return False
