# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import mimetypes

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import html2plaintext

from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)


class MailGatewayWhatsappEvolutionApi(models.AbstractModel):
    _inherit = "mail.gateway.abstract"
    _name = "mail.gateway.whatsapp_evolution_api"
    _description = "WhatsApp Evolution API Gateway"

    def _verify_update(self, bot_data, kwargs):
        webhook_secret = bot_data.get("webhook_secret")
        if not webhook_secret:
            return True
        header_key = request.httprequest.headers.get("webhook_key")
        if not header_key:
            header_key = request.httprequest.headers.get("Webhook-Key")
        return header_key == webhook_secret

    def _set_webhook(self, gateway):
        if not gateway.evolution_api_url or not gateway.token:
            raise UserError(_("Evolution API URL and token are required."))
        payload = {
            "webhook": {
                "enabled": True,
                "url": gateway._get_webhook_url(),
                "byEvents": bool(gateway.evolution_webhook_by_events),
                "events": self._get_webhook_events(gateway),
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
        payload = {"webhook": {"enabled": False}}
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

    def _receive_update(self, gateway, update):
        event = (update.get("event") or "").lower()
        normalized_event = event.replace("_", ".")
        if normalized_event not in {"messages.upsert", "send.message"}:
            return
        data = update.get("data", {})
        message = data.get("message", {})
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
        channel = self._get_channel(gateway, chat_token, data, force_create=True)
        if not channel:
            return
        self._refresh_channel_name(channel, data, chat_token)
        channel = channel.with_context(no_gateway_notification=True)
        body, attachments = self._prepare_message(message, data)
        if not body and not attachments:
            return

        if is_from_me and external_message_id and "mail.notification" in self.env:
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
            if existing_notification:
                return
        author = self._get_author(gateway, data)
        if author and author._name == "mail.guest":
            channel = channel.with_user(self.env.ref("base.public_user").id).with_context(
                guest=author
            )
        log_id = self.env.context.get("gateway_webhook_log_id")
        new_message = channel.sudo().message_post(
            body=body or None,
            author_id=author and author._name == "res.partner" and author.id,
            gateway_type=gateway.gateway_type,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            attachments=attachments,
        )
        if log_id and new_message._fields.get("gateway_webhook_log_id"):
            new_message.sudo().write({"gateway_webhook_log_id": log_id})

        if is_from_me and external_message_id and "mail.notification" in self.env:
            self.env["mail.notification"].sudo().create(
                {
                    "notification_type": "gateway",
                    "mail_message_id": new_message.id,
                    "gateway_channel_id": channel.id,
                    "gateway_type": gateway.gateway_type,
                    "gateway_message_id": external_message_id,
                    "notification_status": "sent",
                }
            )
        self._post_process_message(new_message, channel)

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
                        "gateway_message_id": self._extract_message_id(message),
                    }
                )
        if auto_commit is True:
            # pylint: disable=invalid-commit
            self.env.cr.commit()

    def _apply_outgoing_signature(self, gateway, record, body):
        body = (body or "").strip("\n")
        if not body or not getattr(gateway, "evolution_outgoing_signature", False):
            return body

        author = ""
        mail_message = getattr(record, "mail_message_id", False)
        if mail_message and getattr(mail_message, "author_id", False):
            # Use the raw partner name to avoid display_name prefixing the parent company
            # (e.g. 'YourCompany, Lucas Admin' -> 'Lucas Admin').
            author = (mail_message.author_id.name or "").strip()
        author = author or self.env.user.display_name or self.env.user.name or ""
        author = author.strip()

        fmt = (getattr(gateway, "evolution_outgoing_signature_format", "") or "").strip()
        if not fmt:
            fmt = "*{author}:*\\n"

        # The field is a Char in Odoo UI (single-line). Users may type '\n' to
        # express a new line; convert common escaped sequences.
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
                attachments.append((filename, decoded))
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

    def _get_channel_vals(self, gateway, token, update):
        result = super()._get_channel_vals(gateway, token, update)
        remote_jid, remote_jid_alt, participant_jid = self._extract_jids(update)
        result["name"] = self._get_channel_name(update, token, gateway=gateway)
        if remote_jid_alt:
            result["whatsapp_remote_jid_alt"] = remote_jid_alt
        if participant_jid:
            result["whatsapp_participant_jid"] = participant_jid
        return result

    def _get_author(self, gateway, update):
        data = update or {}
        key_data = data.get("key", {})
        if key_data.get("fromMe"):
            return gateway.webhook_user_id.partner_id
        remote_jid, remote_jid_alt, participant_jid = self._extract_jids(data)
        remote_jid = remote_jid or remote_jid_alt
        if not remote_jid:
            return gateway.webhook_user_id.partner_id
        push_name = data.get("pushName")
        number = self._get_contact_identifier(remote_jid)
        if number:
            linked_partner = self._get_partner_from_gateway_token(gateway, number)
            if linked_partner:
                return linked_partner
        if number:
            partner = self._find_partner_by_number(number)
            if partner:
                self._ensure_gateway_channel_link(partner, gateway, number)
                return partner
        guest = self.env["mail.guest"].search(
            [
                ("gateway_id", "=", gateway.id),
                ("gateway_token", "=", str(remote_jid or "")),
            ],
            limit=1,
        )
        if guest:
            self._update_guest_metadata(
                guest,
                remote_jid=remote_jid,
                remote_jid_alt=remote_jid_alt,
                participant_jid=participant_jid,
                number=number,
                push_name=push_name,
            )
            return guest
        guest = self._get_or_create_guest(
            gateway=gateway,
            remote_jid=remote_jid,
            remote_jid_alt=remote_jid_alt,
            participant_jid=participant_jid,
            number=number,
            push_name=push_name,
        )
        return guest

    def _find_partner_by_number(self, number):
        if not number:
            return False
        partner_domain = [("phone_sanitized", "=", f"+{number}")]
        if "phone_sanitized" not in self.env["res.partner"]._fields:
            partner_domain = ["|", ("phone", "ilike", number), ("mobile", "ilike", number)]
        return self.env["res.partner"].search(partner_domain, limit=1)

    def _get_or_create_guest(
        self,
        gateway,
        remote_jid,
        remote_jid_alt,
        participant_jid,
        number,
        push_name,
    ):
        display_name = self._format_contact_name(push_name, number, remote_jid)
        return self.env["mail.guest"].create(
            {
                "name": display_name,
                "gateway_id": gateway.id,
                "gateway_token": str(remote_jid or ""),
                "whatsapp_remote_jid": remote_jid or "",
                "whatsapp_remote_jid_alt": remote_jid_alt or "",
                "whatsapp_participant_jid": participant_jid or "",
                "whatsapp_number": number or "",
                "last_push_name": push_name or False,
                "last_seen": fields.Datetime.now(),
            }
        )

    def _update_guest_metadata(
        self,
        guest,
        remote_jid,
        remote_jid_alt,
        participant_jid,
        number,
        push_name,
    ):
        vals = {}
        now = fields.Datetime.now()
        vals["last_seen"] = now
        if remote_jid and guest.whatsapp_remote_jid != remote_jid:
            vals["whatsapp_remote_jid"] = remote_jid
        if remote_jid_alt and guest.whatsapp_remote_jid_alt != remote_jid_alt:
            vals["whatsapp_remote_jid_alt"] = remote_jid_alt
        if participant_jid and guest.whatsapp_participant_jid != participant_jid:
            vals["whatsapp_participant_jid"] = participant_jid
        if number and guest.whatsapp_number != number:
            vals["whatsapp_number"] = number
        if push_name and guest.last_push_name != push_name:
            vals["last_push_name"] = push_name
            # Atualiza o nome se ele ainda refletir o valor anterior ou estiver vazio.
            if guest.name in {guest.last_push_name, guest.whatsapp_number, guest.whatsapp_remote_jid, False, ""}:
                vals["name"] = self._format_contact_name(push_name, number, remote_jid)
        if vals:
            guest.sudo().write(vals)

    def _ensure_gateway_channel_link(self, partner, gateway, token):
        existing = self.env["res.partner.gateway.channel"].search(
            [
                ("partner_id", "=", partner.id),
                ("gateway_id", "=", gateway.id),
            ],
            limit=1,
        )
        if not existing:
            self.env["res.partner.gateway.channel"].create(
                {
                    "partner_id": partner.id,
                    "gateway_id": gateway.id,
                    "gateway_token": str(token),
                }
            )

    def _get_channel_name(self, data, token, gateway=None):
        key_data = data.get("key", {}) or {}
        remote_jid = key_data.get("remoteJid") or data.get("remoteJid") or token
        push_name = data.get("pushName")
        from_me = bool(key_data.get("fromMe"))
        number = self._get_contact_identifier(remote_jid)
        if remote_jid and remote_jid.endswith("@g.us"):
            group_name = (
                (data.get("group") or {}).get("subject")
                or (data.get("groupMetadata") or {}).get("subject")
                or (data.get("chat") or {}).get("subject")
            )
            if group_name:
                return group_name
            return f"Group: {remote_jid.split('@')[0]}"
        if gateway and number:
            linked_partner = self._get_partner_from_gateway_token(gateway, number)
            if linked_partner:
                return self._format_contact_name(linked_partner.name, number, remote_jid)
            partner = self._find_partner_by_number(number)
            if partner:
                self._ensure_gateway_channel_link(partner, gateway, number)
                return self._format_contact_name(partner.name, number, remote_jid)
        if not from_me:
            return self._format_contact_name(push_name, number, remote_jid)
        return self._format_contact_name(False, number, remote_jid)

    def _format_contact_name(self, push_name, number, remote_jid):
        clean_name = (push_name or "").strip()
        if clean_name:
            return clean_name
        if number:
            return number
        if remote_jid:
            return remote_jid
        return "WhatsApp"

    def _refresh_channel_name(self, channel, data, token):
        desired_name = self._get_channel_name(data, token, gateway=channel.gateway_id)
        if not desired_name or channel.name == desired_name:
            return
        gateway = channel.gateway_id
        push_name = data.get("pushName")
        guest = False
        if gateway and token:
            guest = self.env["mail.guest"].search(
                [
                    ("gateway_id", "=", gateway.id),
                    ("gateway_token", "=", str(token)),
                ],
                limit=1,
            )
        auto_names = {
            gateway.name if gateway else False,
            gateway.evolution_instance if gateway else False,
            push_name,
            token,
        }
        if guest:
            auto_names.update(
                {
                    guest.name,
                    guest.last_push_name,
                    guest.whatsapp_number,
                    guest.whatsapp_remote_jid,
                }
            )
        if channel.name and channel.name not in auto_names and not channel.name.startswith(
            ("WhatsApp:", "WhatsApp Group:", "Group:")
        ):
            return
        channel.sudo().write({"name": desired_name})

    def _extract_jids(self, data):
        if not isinstance(data, dict):
            return False, False, False
        key_data = data.get("key", {}) or {}
        remote_jid = key_data.get("remoteJid")
        remote_jid_alt = key_data.get("remoteJidAlt")
        participant_jid = key_data.get("participant")
        return remote_jid, remote_jid_alt, participant_jid

    def _get_partner_from_gateway_token(self, gateway, token):
        if not gateway or not token:
            return False
        link = self.env["res.partner.gateway.channel"].search(
            [("gateway_id", "=", gateway.id), ("gateway_token", "=", str(token))],
            limit=1,
        )
        return link.partner_id if link else False

    def _get_chat_token(self, data):
        remote_jid, remote_jid_alt, _participant_jid = self._extract_jids(data)
        if not remote_jid:
            return False
        return remote_jid

    def _get_contact_identifier(self, remote_jid):
        if not remote_jid:
            return False
        if not isinstance(remote_jid, str):
            return False
        if remote_jid.endswith("@g.us"):
            return False
        if not remote_jid.endswith("@s.whatsapp.net"):
            return False
        whatsapp_number = remote_jid.split("@")[0]
        if not whatsapp_number.isdigit():
            return False
        return whatsapp_number

    def _get_attachment_name(self, message, key, data):
        name = (
            message.get(key, {}).get("fileName")
            or message.get(key, {}).get("title")
            or data.get("key", {}).get("id")
            or "attachment"
        )
        mimetype = message.get(key, {}).get("mimetype")
        if mimetype and "." not in name:
            extension = mimetypes.guess_extension(mimetype) or ""
            name = f"{name}{extension}"
        return name

    def _decode_base64_payload(self, payload):
        if not payload:
            return None
        if isinstance(payload, dict):
            payload = payload.get("base64")
        if not payload:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if payload.startswith("data:") and "," in payload:
            payload = payload.split(",", 1)[1]
        try:
            return base64.b64decode(payload)
        except Exception:
            _logger.warning("Invalid base64 payload received")
            return None

    def _get_webhook_events(self, gateway):
        if gateway.evolution_webhook_event_ids:
            return [
                event.code
                for event in gateway.evolution_webhook_event_ids
                if event.code
            ]
        if (
            not self.env["mail.gateway.whatsapp_evolution_api.webhook_event"].search_count([])
        ):
            return ["MESSAGES_UPSERT", "CONNECTION_UPDATE", "QRCODE_UPDATED"]
        return []

    def _instance_name(self, gateway):
        return gateway.evolution_instance or gateway.name

    def _get_headers(self, gateway):
        return {"Content-Type": "application/json", "apikey": gateway.token}

    def _join_url(self, base_url, endpoint):
        return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _send_api_request(self, gateway, method, endpoint, payload):
        # Keep method/payload aligned with EVOLUTION_API_REFERENCE.md.
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

    def _format_payload(self, payload):
        if payload is None:
            return False
        try:
            return json.dumps(payload, ensure_ascii=True, indent=2)
        except (TypeError, ValueError):
            return str(payload)

    def _extract_message_id(self, payload):
        if not isinstance(payload, dict):
            return False
        message_id = payload.get("id") or payload.get("message_id")
        if not message_id:
            message_id = (payload.get("key") or {}).get("id")
        return message_id

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
