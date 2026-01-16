# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import mimetypes

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
        event = (update.get("event") or "").lower()
        normalized_event = event.replace("_", ".")
        if normalized_event not in {"messages.upsert", "send.message"}:
            return
        data = update.get("data", {}) or {}
        message = data.get("message", {}) or {}
        if not data or not message:
            return

        key_data = data.get("key", {}) or {}
        is_from_me = bool(key_data.get("fromMe"))
        external_message_id = key_data.get("id")
        if normalized_event == "send.message" and not is_from_me:
            return
        chat_token = self._get_chat_token(data)
        if not chat_token:
            return
        channel = self._get_channel(gateway, chat_token, data)
        if not channel:
            return
        self._refresh_channel_name(channel, data, chat_token)

        dto = self._build_dto_from_evolution(update, gateway, channel)
        if not dto or not dto.message_id:
            return

        common = self.env["mail.gateway.whatsapp.common"]
        msg = common._process_normalized(gateway, dto, channel, author=None)

        if msg and is_from_me and external_message_id and "mail.notification" in self.env:
            existing_notification = (
                self.env["mail.notification"]
                .sudo()
                .search(
                    [
                        ("notification_type", "=", "gateway"),
                        ("gateway_type", "=", gateway.gateway_type),
                        ("gateway_channel_id", "=", channel.id),
                        ("gateway_message_id", "=", external_message_id),
                    ],
                    limit=1,
                )
            )
            if not existing_notification:
                self.env["mail.notification"].sudo().create(
                    {
                        "notification_type": "gateway",
                        "mail_message_id": msg.id,
                        "gateway_channel_id": channel.id,
                        "gateway_type": gateway.gateway_type,
                        "gateway_message_id": external_message_id,
                        "notification_status": "sent",
                    }
                )

        if msg:
            self._post_process_message(msg, channel)

    def _build_dto_from_evolution(self, update, gateway, channel):
        data = update.get("data", {}) or {}
        message = data.get("message", {}) or {}
        key_data = data.get("key", {}) or {}
        body, attachments = self._prepare_message(message, data)
        event = (update.get("event") or "message_upsert").lower()
        normalized_event = event.replace("_", ".")
        dto_event = "message_upsert" if "message" in normalized_event else normalized_event
        chat_id = self._get_chat_token(data)
        return NormalizedPayload(
            provider="evolution",
            instance=self._instance_name(gateway),
            event=dto_event,
            message_id=key_data.get("id"),
            chat_id=chat_id,
            from_me=bool(key_data.get("fromMe")),
            sender_jid=key_data.get("participant") or key_data.get("remoteJid"),
            sender_jid_alt=key_data.get("remoteJidAlt"),
            sender_participant_jid=key_data.get("participant"),
            sender_name=data.get("pushName"),
            timestamp=message.get("messageTimestamp") or data.get("timestamp"),
            message_type=message.get("messageType") or message.get("type"),
            text=body,
            caption=message.get("caption"),
            attachments=attachments,
            quote_id=(data.get("quotedMessage") or {}).get("stanzaId") or data.get("quotedStanzaID"),
            quote_text=(data.get("quotedMessage") or {}).get("text"),
            reaction=data.get("reaction"),
            reaction_target_id=data.get("reactionMessageId") or data.get("messageId"),
            status=data.get("status"),
            status_raw=data.get("status_raw"),
            raw=update,
        )

    def _prepare_message(self, message, data):
        body = ""
        attachments = []
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
        return body, attachments

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _get_channel(self, gateway, chat_token, data):
        channel = self.env["discuss.channel"].sudo().search(
            [
                ("channel_type", "=", "gateway"),
                ("gateway_id", "=", gateway.id),
                ("gateway_channel_token", "=", chat_token),
            ],
            limit=1,
        )
        if channel:
            return channel
        vals = {
            "name": self._get_channel_name(data, chat_token, gateway=gateway),
            "channel_type": "gateway",
            "gateway_id": gateway.id,
            "gateway_channel_token": chat_token,
        }
        return self.env["discuss.channel"].sudo().create(vals)

    def _get_channel_name(self, data, token, gateway=None):
        remote_jid, remote_jid_alt, participant_jid = self._extract_jids(data)
        name = remote_jid or remote_jid_alt or token
        push = data.get("pushName") or data.get("name")
        if push:
            name = push
        return name

    def _refresh_channel_name(self, channel, data, token):
        # Minimal refresh: update name if empty or equals token
        desired = self._get_channel_name(data, token, gateway=channel.gateway_id)
        if desired and channel.name != desired:
            channel.sudo().write({"name": desired})


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
        if auto_commit:
            record._cr.commit()

    def _join_url(self, base_url, endpoint):
        return f"{(base_url or '').rstrip('/')}/{endpoint.lstrip('/')}"

    def _get_message_body(self, record):
        return record.mail_message_id.body

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
        log_record = self._create_webhook_log(
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

    def _create_webhook_log(
        self,
        gateway,
        direction,
        status,
        payload=None,
        event=None,
        endpoint=None,
    ):
        if "mail.gateway.webhook.log" not in self.env:
            return False
        if not self._is_webhook_logging_enabled():
            return False
        payload_text = self._format_payload(payload)
        return (
            self.env["mail.gateway.webhook.log"]
            .sudo()
            .create(
                {
                    "gateway_id": gateway.id if gateway else False,
                    "direction": direction,
                    "status": status,
                    "event": event,
                    "endpoint": endpoint,
                    "request_payload": payload_text,
                }
            )
        )

    def _is_webhook_logging_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.webhook_log_enabled", default="1"
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    def _format_payload(self, payload):
        if payload is None:
            return False
        try:
            return json.dumps(payload, ensure_ascii=True, indent=2)
        except (TypeError, ValueError):
            return str(payload)
