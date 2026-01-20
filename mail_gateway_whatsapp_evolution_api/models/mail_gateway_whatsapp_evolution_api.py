# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import mimetypes
from urllib.parse import quote

import requests

from odoo import _, models
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import html2plaintext

from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.addons.mail_gateway_whatsapp_common.models.normalized_payload import (
    NormalizedPayload,
)

_logger = logging.getLogger(__name__)


class MailGatewayWhatsappEvolutionApi(models.AbstractModel):
    _name = "mail.gateway.whatsapp_evolution_api"
    _inherit = ["mail.gateway.abstract", "mail.gateway.whatsapp_evolution_api.mixin"]
    _description = "WhatsApp Evolution API Gateway"

    # -------------------------------------------------------------------------
    # Webhook / verification
    # -------------------------------------------------------------------------
    def _verify_update(self, bot_data, kwargs):
        webhook_secret = bot_data.get("webhook_secret")
        if not webhook_secret:
            return True
        header_key = request.httprequest.headers.get("webhook_key") or request.httprequest.headers.get(
            "Webhook-Key"
        )
        return header_key == webhook_secret

    def _set_webhook(self, gateway):
        if not gateway.evolution_api_url or not gateway.token:
            raise UserError(_("Evolution API URL and token are required."))
        events = gateway._get_webhook_events()
        payload = {
            "webhook": {
                "enabled": True,
                "url": gateway._get_webhook_url(),
                "byEvents": bool(gateway.evolution_webhook_by_events),
                "events": events,
                "base64": bool(gateway.evolution_base64_webhook),
            }
        }
        if gateway.webhook_secret:
            payload["webhook"]["headers"] = {"webhook_key": gateway.webhook_secret}
        self._send_api_request(gateway, "POST", f"/webhook/set/{self._instance_name(gateway)}", payload)
        gateway.integrated_webhook_state = "integrated"

    def _remove_webhook(self, gateway):
        if not gateway.evolution_api_url or not gateway.token:
            gateway.integrated_webhook_state = False
            return
        payload = {
            "webhook": {
                "enabled": False,
                "url": gateway._get_webhook_url(),
                "byEvents": bool(gateway.evolution_webhook_by_events),
                "events": gateway._get_webhook_events(),
                "base64": bool(gateway.evolution_base64_webhook),
            }
        }
        if gateway.webhook_secret:
            payload["webhook"]["headers"] = {"webhook_key": gateway.webhook_secret}
        try:
            self._send_api_request(
                gateway,
                "POST",
                f"/webhook/set/{self._instance_name(gateway)}",
                payload,
            )
        except Exception as exc:
            _logger.warning("Failed to disable webhook: %s", exc)
        gateway.integrated_webhook_state = False

    # -------------------------------------------------------------------------
    # Incoming
    # -------------------------------------------------------------------------
    def _receive_update(self, gateway, update):
        canonical_event = self._normalize_event(update)
        if not canonical_event:
            return {"status": "ignored", "reason": "event_not_supported"}
        data = update.get("data", {}) or {}
        if isinstance(data, list):
            results = []
            for item in data:
                if not item:
                    continue
                item_update = dict(update)
                item_update["data"] = item
                results.append(
                    self._receive_update_item(gateway, item_update, canonical_event)
                )
            if not results:
                return {"status": "ignored", "reason": "missing_data"}
            status = "ok" if any(
                result.get("status") in ("ok", "duplicate") for result in results
            ) else "ignored"
            return {"status": status, "results": results}
        return self._receive_update_item(gateway, update, canonical_event)

    def _receive_update_item(self, gateway, update, canonical_event=None):
        canonical_event = canonical_event or self._normalize_event(update)
        if not canonical_event:
            return {"status": "ignored", "reason": "event_not_supported"}
        data = update.get("data", {}) or {}
        if not data:
            return {"status": "ignored", "reason": "missing_data"}
        if canonical_event == "message.upsert":
            message = data.get("message", {}) or {}
            if not message:
                return {"status": "ignored", "reason": "missing_message"}
        dto = self._build_dto_from_evolution(
            update, gateway, None, canonical_event=canonical_event
        )
        if not dto:
            return {"status": "ignored", "reason": "normalization_failed"}

        common = self.env["mail.gateway.whatsapp.common"]
        return common._process_normalized(gateway, dto, None, author=None)

    def _build_dto_from_evolution(self, update, gateway, channel, canonical_event=None):
        data = update.get("data", {}) or {}
        if isinstance(data, list):
            data = data[0] if data else {}
        message = data.get("message", {}) or {}
        key_data = data.get("key", {}) or {}
        body, attachments, text_is_html = self._prepare_message(message, data)
        dto_event = canonical_event or self._normalize_event(update)
        if not dto_event:
            return False
        if dto_event == "contact.update":
            return self._build_contact_dto(update, gateway, data)
        if dto_event == "chat.update":
            return self._build_chat_dto(update, gateway, data)
        reaction, reaction_target_id = self._extract_reaction_data(data, message)
        message_id = self._get_message_id(data, key_data)
        chat_id = self._get_chat_token(data)
        is_group = self._is_group_chat(chat_id)
        sender_name = data.get("pushName") or data.get("name")
        chat_name, chat_description, chat_picture_url = self._get_group_metadata(
            update, gateway, chat_id, sender_name, dto_event
        )
        return NormalizedPayload(
            provider="evolution",
            instance=self._instance_name(gateway),
            event=dto_event,
            message_id=message_id,
            chat_id=chat_id,
            chat_name=chat_name,
            chat_description=chat_description,
            chat_picture_url=chat_picture_url,
            is_group=is_group,
            from_me=bool(key_data.get("fromMe")),
            sender_jid=key_data.get("participant") or key_data.get("remoteJid"),
            sender_jid_alt=key_data.get("participantAlt") or key_data.get("remoteJidAlt"),
            sender_participant_jid=key_data.get("participant"),
            sender_name=sender_name,
            timestamp=message.get("messageTimestamp") or data.get("timestamp"),
            message_type=message.get("messageType")
            or data.get("messageType")
            or message.get("type"),
            text=body,
            text_is_html=text_is_html,
            caption=message.get("caption"),
            attachments=attachments,
            quote_id=(data.get("quotedMessage") or {}).get("stanzaId") or data.get("quotedStanzaID"),
            quote_text=(data.get("quotedMessage") or {}).get("text"),
            reaction=reaction,
            reaction_target_id=reaction_target_id,
            status=data.get("status") or data.get("status_raw"),
            status_raw=data.get("status_raw") or data.get("status"),
            raw=update,
        )

    def _build_contact_dto(self, update, gateway, data):
        contact_jid = data.get("remoteJid")
        contact_name = data.get("pushName")
        contact_pic = data.get("profilePicUrl")
        return NormalizedPayload(
            provider="evolution",
            instance=self._instance_name(gateway),
            event="contact.update",
            chat_id=contact_jid,
            contact_jid=contact_jid,
            contact_name=contact_name,
            contact_profile_pic_url=contact_pic,
            sender_name=contact_name,
            is_group=self._is_group_chat(contact_jid),
            raw=update,
        )

    def _build_chat_dto(self, update, gateway, data):
        chat_id = data.get("remoteJid")
        return NormalizedPayload(
            provider="evolution",
            instance=self._instance_name(gateway),
            event="chat.update",
            chat_id=chat_id,
            chat_name=data.get("name"),
            chat_unread_count=data.get("unreadMessages"),
            is_group=self._is_group_chat(chat_id),
            raw=update,
        )

    def _prepare_message(self, message, data):
        body = ""
        attachments = []
        text_is_html = False
        if message.get("conversation"):
            body = message.get("conversation")
        elif message.get("extendedTextMessage"):
            body = message.get("extendedTextMessage", {}).get("text", "")
        for key in [
            "imageMessage",
            "videoMessage",
            "audioMessage",
            "documentMessage",
            "stickerMessage",
        ]:
            if not message.get(key):
                continue
            caption = message.get(key, {}).get("caption", "")
            if caption:
                body = caption
            payload_base64 = message.get("base64") or message.get(key, {}).get("base64")
            decoded = self._decode_base64_payload(payload_base64)
            if decoded:
                filename = self._get_attachment_name(message, key, data)
                attachments.append(
                    {
                        "name": filename,
                        "datas": decoded,
                        "mimetype": message.get(key, {}).get("mimetype")
                        or message.get(key, {}).get("mimetype", ""),
                    }
                )
        if message.get("locationMessage"):
            location = message.get("locationMessage", {})
            latitude = location.get("degreesLatitude")
            longitude = location.get("degreesLongitude")
            if latitude and longitude:
                body = (
                    f'<a target="_blank" href="https://www.google.com/maps/'
                    f"search/?api=1&query={latitude},{longitude}\">Location</a>"
                )
                text_is_html = True
        return body, attachments, text_is_html

    def _get_group_metadata(self, update, gateway, chat_id, sender_name, event):
        if not self._is_group_chat(chat_id):
            return None, None, None
        payload_name, payload_desc, payload_picture = (
            self._extract_group_metadata_from_payload(update)
        )
        if payload_name or payload_desc or payload_picture:
            return payload_name, payload_desc, payload_picture
        if event != "message.upsert":
            return None, None, None
        if not self._should_fetch_group_info(gateway, chat_id, sender_name):
            return None, None, None
        info = self._fetch_group_info(gateway, chat_id)
        if not info:
            return None, None, None
        return (
            info.get("subject") or info.get("name"),
            info.get("desc") or info.get("description"),
            info.get("pictureUrl") or info.get("picture_url"),
        )

    def _extract_group_metadata_from_payload(self, update):
        data = update.get("data", {}) or {}
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            return None, None, None
        return (
            data.get("subject") or data.get("name"),
            data.get("desc") or data.get("description"),
            data.get("pictureUrl") or data.get("profilePicUrl"),
        )

    def _should_fetch_group_info(self, gateway, chat_id, sender_name):
        if not gateway or not chat_id:
            return True
        channel_id = gateway._get_channel_id(chat_id)
        if not channel_id:
            return True
        channel = self.env["discuss.channel"].browse(channel_id)
        if not channel:
            return True
        fallback_group = self.env["mail.gateway.whatsapp.common"]._format_group_name(chat_id)
        fallback_chat = self.env["mail.gateway.whatsapp.common"]._format_chat_id(chat_id)
        current_name = (channel.name or "").strip()
        sender_name = (sender_name or "").strip()
        if not current_name or current_name in {fallback_group, fallback_chat}:
            return True
        if sender_name and current_name == sender_name:
            return True
        if not channel.description or not channel.image_128:
            return True
        return False

    def _fetch_group_info(self, gateway, chat_id):
        if not gateway or not chat_id:
            return False
        instance = self._instance_name(gateway)
        endpoint = f"/group/findGroupInfos/{instance}?groupJid={quote(chat_id)}"
        try:
            return self._send_api_request(gateway, "GET", endpoint)
        except Exception as exc:
            _logger.warning("Failed to fetch group info: %s", exc)
            return False

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _normalize_event(self, update):
        event = (update.get("event") or "").lower()
        normalized_event = event.replace("_", ".")
        if normalized_event in {
            "message.upsert",
            "message.status",
            "message.delete",
            "reaction.upsert",
            "reaction.delete",
        }:
            return normalized_event
        if normalized_event in {"contacts.update", "contacts.upsert", "contact.update"}:
            return "contact.update"
        if normalized_event in {"chats.update", "chats.upsert", "chat.update"}:
            return "chat.update"

        data = update.get("data", {}) or {}
        if isinstance(data, list):
            data = data[0] if data else {}
        message = data.get("message", {}) or {}
        reaction, reaction_target_id = self._extract_reaction_data(data, message)

        if normalized_event == "messages.upsert":
            if reaction_target_id:
                return "reaction.delete" if not reaction else "reaction.upsert"
            return "message.upsert"
        if normalized_event == "send.message":
            return "message.upsert"
        if normalized_event == "messages.update":
            return "message.status"
        if normalized_event == "messages.delete":
            return "message.delete"
        return None

    @staticmethod
    def _is_group_chat(chat_id):
        return str(chat_id or "").endswith("@g.us")

    def _extract_reaction_data(self, data, message):
        reaction = None
        reaction_target_id = None
        reaction_message = message.get("reactionMessage") if isinstance(message, dict) else None
        if isinstance(reaction_message, dict):
            reaction = reaction_message.get("text")
            if isinstance(reaction, str):
                reaction = reaction.strip()
            reaction_key = reaction_message.get("key") or {}
            reaction_target_id = reaction_key.get("id")
            return reaction, reaction_target_id

        if "reaction" in data:
            reaction = data.get("reaction")
            if isinstance(reaction, str):
                reaction = reaction.strip()
            reaction_target_id = data.get("reactionMessageId") or data.get("messageId")
        return reaction, reaction_target_id

    @staticmethod
    def _get_message_id(data, key_data):
        message_id = key_data.get("id")
        if message_id:
            return message_id
        message_id = data.get("keyId") or data.get("id") or data.get("messageId")
        if isinstance(message_id, list):
            message_id = message_id[0] if message_id else None
        return message_id

    def _decode_base64_payload(self, payload):
        if not payload:
            return False
        if isinstance(payload, bytes):
            return base64.b64encode(payload).decode()
        if isinstance(payload, str):
            return payload
        return False

    def _get_attachment_name(self, message, key, data):
        if message.get("fileName"):
            return message.get("fileName")
        if message.get(key, {}).get("fileName"):
            return message.get(key, {}).get("fileName")
        return f"{key}.bin"

    def _apply_outgoing_signature(self, gateway, record, body):
        if not gateway.evolution_outgoing_signature or not record.author_id:
            return body
        author = record.author_id.name or ""
        author = author.strip()
        fmt = (getattr(gateway, "evolution_outgoing_signature_format", "") or "").strip()
        if not fmt:
            fmt = "*{author}:*\\n"
        fmt = fmt.replace("\\n", "\n").replace("\\t", "\t")
        try:
            prefix = fmt.format(author=author)
        except Exception:
            prefix = "*{author}:*\\n".format(author=author)
        if not prefix:
            return body
        normalized_body = body.lstrip()
        if normalized_body.startswith(prefix):
            return body
        return f"{prefix}{body}"

    def _get_chat_token(self, data):
        remote_jid, remote_jid_alt, participant_jid = self._extract_jids(data)
        return remote_jid or remote_jid_alt or participant_jid

    def _extract_jids(self, data):
        key_data = data.get("key", {}) or {}
        return (
            key_data.get("remoteJid"),
            key_data.get("remoteJidAlt"),
            key_data.get("participant"),
        )

    # -------------------------------------------------------------------------
    # Outgoing
    # -------------------------------------------------------------------------
    def _get_headers(self, gateway):
        return {"Content-Type": "application/json", "apikey": gateway.token}

    def _instance_name(self, gateway):
        return gateway.evolution_instance or gateway.name

    def _send(
        self,
        gateway,
        record,
        auto_commit=False,
        raise_exception=False,
        parse_mode=False,
    ):
        message = False
        try:
            channel = record.gateway_channel_id
            number = channel.gateway_channel_token
            instance = self._instance_name(gateway)
            headers = self._get_headers(gateway)
            for attachment in record.mail_message_id.attachment_ids:
                media_type = self._guess_media_type(attachment.mimetype)
                payload = {
                    "number": number,
                    "mediatype": media_type,
                    "mimetype": attachment.mimetype,
                    "media": attachment.datas,
                    "fileName": attachment.name or "attachment",
                }
                response = requests.post(
                    self._join_url(gateway.evolution_api_url, f"/message/sendMedia/{instance}"),
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                message = response.json() if response.content else {}
            body = html2plaintext(self._get_message_body(record))
            if body:
                body = self._apply_outgoing_signature(gateway, record, body)
                payload = {"number": number, "text": body}
                response = requests.post(
                    self._join_url(gateway.evolution_api_url, f"/message/sendText/{instance}"),
                    json=payload,
                    headers=headers,
                    timeout=20,
                )
                response.raise_for_status()
                message = response.json() if response.content else {}
        except Exception as exc:
            _logger.exception("Unable to send Evolution message")
            if raise_exception:
                raise MailDeliveryException(
                    _("Unable to send the Evolution message")
                ) from exc
            record.sudo().write(
                {
                    "notification_status": "exception",
                    "failure_reason": str(exc),
                }
            )
        else:
            if message:
                record.sudo().write(
                    {
                        "notification_status": "sent",
                        "failure_reason": False,
                    }
                )
                message_id = self._extract_message_id_from_response(message)
                if message_id:
                    self._update_outgoing_message(
                        record, gateway, message_id, instance, number
                    )
        if auto_commit:
            record._cr.commit()

    def _join_url(self, base_url, endpoint):
        return f"{(base_url or '').rstrip('/')}/{endpoint.lstrip('/')}"

    def _get_message_body(self, record):
        return record.mail_message_id.body

    def _extract_message_id_from_response(self, payload):
        if not payload:
            return False
        if isinstance(payload, dict):
            key_data = payload.get("key") or {}
            message_id = key_data.get("id")
            if message_id:
                return message_id
            message_id = payload.get("messageId") or payload.get("id")
            if isinstance(message_id, list):
                message_id = message_id[0] if message_id else None
            if message_id:
                return message_id
            message_data = payload.get("message") or {}
            if isinstance(message_data, dict):
                key_data = message_data.get("key") or {}
                message_id = key_data.get("id")
                if message_id:
                    return message_id
                message_id = message_data.get("messageId") or message_data.get("id")
                if isinstance(message_id, list):
                    message_id = message_id[0] if message_id else None
                if message_id:
                    return message_id
        return False

    def _build_message_key(self, gateway, instance, chat_id, message_id):
        parts = [
            gateway.gateway_type or "",
            str(gateway.id or ""),
            instance or "",
            chat_id or "",
            message_id or "",
        ]
        return "|".join(parts)

    def _update_outgoing_message(self, record, gateway, message_id, instance, chat_id):
        mail_message = record.mail_message_id.sudo()
        if not mail_message or not message_id:
            return
        message_key = self._build_message_key(gateway, instance, chat_id, message_id)
        if message_key:
            existing = (
                self.env["mail.message"]
                .sudo()
                .search([("gateway_message_key", "=", message_key)], limit=1)
            )
            if existing and existing.id != mail_message.id:
                return
        sender_name = (
            mail_message.author_id.name
            or mail_message.author_guest_id.name
            or False
        )
        update_vals = {
            "gateway_message_external_id": message_id,
            "gateway_message_key": message_key,
            "gateway_instance": instance,
            "gateway_chat_id": chat_id,
            "gateway_from_me": True,
            "gateway_type": gateway.gateway_type,
        }
        if sender_name:
            update_vals["gateway_sender_name"] = sender_name
        mail_message.write(update_vals)
        record.sudo().write({"gateway_message_id": message_id})

    def _guess_media_type(self, mimetype):
        if not mimetype:
            return "document"
        if mimetype.startswith("image/"):
            return "image"
        if mimetype.startswith("video/"):
            return "video"
        if mimetype.startswith("audio/"):
            return "audio"
        return "document"

    # -------------------------------------------------------------------------
    # API request (wrapper)
    # -------------------------------------------------------------------------
    def _send_api_request(self, gateway, method, endpoint, payload=None):
        log_record = self._devtools_log_webhook(
            gateway,
            direction="out",
            status="sending",
            endpoint=endpoint,
            payload=payload,
        )
        return self._evolution_api_request(
            gateway.evolution_api_url,
            gateway.token,
            method,
            endpoint,
            payload=payload,
            log_record=log_record,
        )

    def _devtools_log_webhook(
        self,
        gateway,
        direction,
        status,
        payload=None,
        event=None,
        endpoint=None,
    ):
        return False
