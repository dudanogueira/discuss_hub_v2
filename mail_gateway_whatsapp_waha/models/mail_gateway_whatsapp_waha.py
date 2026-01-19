# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re

import requests

from odoo import _, models
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import html2plaintext

from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)


class MailGatewayWhatsappWaha(models.AbstractModel):
    _name = "mail.gateway.whatsapp_waha"
    _inherit = "mail.gateway.abstract"
    _description = "WhatsApp WAHA Gateway"

    def _receive_get_update(self, bot_data, req, **kwargs):
        response = request.make_response(
            "{}",
            [
                ("Content-Type", "application/json"),
            ],
        )
        response.status_code = 200
        return response

    def _receive_update(self, gateway, update):
        return {"status": "ignored", "reason": "not_implemented"}

    def _verify_update(self, bot_data, kwargs):
        return True

    def _send(
        self,
        gateway,
        record,
        auto_commit=False,
        raise_exception=False,
        parse_mode=False,
    ):
        message = False
        chat_id = False
        session = False
        try:
            self._ensure_gateway_ready(gateway)
            session = gateway.waha_session or "default"
            channel = record.gateway_channel_id
            chat_id = self._normalize_chat_id(channel.gateway_channel_token)
            body = html2plaintext(self._get_message_body(record) or "").strip()
            if record.mail_message_id.attachment_ids:
                raise UserError(_("WAHA media sending is not supported yet."))
            if not body:
                raise UserError(_("Message body is empty."))
            payload = {
                "session": session,
                "chatId": chat_id,
                "text": body,
            }
            response = requests.post(
                self._join_url(gateway.waha_api_url, "/api/sendText"),
                json=payload,
                headers=self._get_headers(gateway),
                timeout=20,
            )
            response.raise_for_status()
            message = response.json() if response.content else {}
        except Exception as exc:
            _logger.exception("Unable to send WAHA message")
            if raise_exception:
                raise MailDeliveryException(_("Unable to send the WAHA message")) from exc
            record.sudo().write(
                {
                    "notification_status": "exception",
                    "failure_reason": str(exc),
                }
            )
        else:
            record.sudo().write(
                {
                    "notification_status": "sent",
                    "failure_reason": False,
                }
            )
            message_id = self._extract_message_id_from_response(message)
            if message_id:
                self._update_outgoing_message(record, gateway, message_id, session, chat_id)
        if auto_commit:
            record._cr.commit()

    def _ensure_gateway_ready(self, gateway):
        if not gateway.waha_api_url or not gateway.token:
            raise UserError(_("WAHA API URL and API key are required."))

    def _get_headers(self, gateway):
        return {
            "Content-Type": "application/json",
            "X-Api-Key": gateway.token,
        }

    def _join_url(self, base_url, endpoint):
        return f"{(base_url or '').rstrip('/')}/{endpoint.lstrip('/')}"

    def _normalize_chat_id(self, chat_id):
        if not chat_id:
            return ""
        chat_id = chat_id.strip()
        if "@" in chat_id:
            return chat_id
        digits = re.sub(r"\D", "", chat_id)
        if digits:
            return f"{digits}@c.us"
        return chat_id

    def _extract_message_id_from_response(self, payload):
        if not payload:
            return False
        if isinstance(payload, dict):
            candidates = [
                payload.get("_data", {}).get("id", {}).get("_serialized"),
                payload.get("id", {}).get("_serialized"),
                payload.get("_data", {}).get("id", {}).get("id"),
                payload.get("id", {}).get("id"),
                payload.get("id"),
                payload.get("messageId"),
            ]
            for candidate in candidates:
                if candidate:
                    return candidate
        return False

    def _build_message_key(self, gateway, session, chat_id, message_id):
        parts = [
            gateway.gateway_type or "",
            str(gateway.id or ""),
            session or "",
            chat_id or "",
            message_id or "",
        ]
        return "|".join(parts)

    def _update_outgoing_message(self, record, gateway, message_id, session, chat_id):
        mail_message = record.mail_message_id.sudo()
        if not mail_message or not message_id:
            return
        message_key = self._build_message_key(gateway, session, chat_id, message_id)
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
            "gateway_instance": session,
            "gateway_chat_id": chat_id,
            "gateway_from_me": True,
            "gateway_type": gateway.gateway_type,
        }
        if sender_name:
            update_vals["gateway_sender_name"] = sender_name
        mail_message.write(update_vals)
        record.sudo().write({"gateway_message_id": message_id})
