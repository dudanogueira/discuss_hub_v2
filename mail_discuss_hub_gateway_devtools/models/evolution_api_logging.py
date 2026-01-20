# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import models
from odoo.http import request


class MailGatewayWhatsappEvolutionApi(models.AbstractModel):
    _inherit = "mail.gateway.whatsapp_evolution_api"

    def _receive_update(self, gateway, update):
        log_record = self._devtools_log_webhook(
            gateway,
            direction="in",
            status="received",
            event=update.get("event") if isinstance(update, dict) else None,
            endpoint=self._devtools_inbound_endpoint(),
            payload=update,
        )
        dispatcher = self
        if log_record:
            dispatcher = dispatcher.with_context(gateway_webhook_log_id=log_record.id)
        try:
            result = super(
                MailGatewayWhatsappEvolutionApi, dispatcher
            )._receive_update(gateway, update) or {}
        except Exception as exc:
            if log_record:
                log_record.sudo().write(
                    {
                        "status": "error",
                        "error_message": str(exc),
                    }
                )
            raise
        if log_record:
            status = (
                "processed"
                if result.get("status") in ("ok", "duplicate")
                else "received"
            )
            log_record.sudo().write({"status": status})
        return result

    def _send_outbound(self, gateway, dto):
        log_record = self._devtools_log_webhook(
            gateway,
            direction="out",
            status="sending",
            event="message.send",
            endpoint=self._devtools_outgoing_endpoint(gateway, dto),
            payload=self._devtools_outgoing_payload(gateway, dto),
        )
        if log_record:
            log_record.sudo().write(
                {
                    "internal_routine": "send_message",
                    "internal_result": "received",
                }
            )
        try:
            res = super()._send_outbound(gateway, dto)
        except Exception as exc:
            if log_record:
                log_record.sudo().write(
                    {
                        "status": "error",
                        "error_message": str(exc),
                    }
                )
            raise

        if log_record:
            log_record.sudo().write(
                {
                    "status": "sent",
                    "internal_result": "processed",
                }
            )
        return res

    @staticmethod
    def _devtools_inbound_endpoint():
        try:
            return request.httprequest.path
        except Exception:
            return False

    def _devtools_log_webhook(
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
        if not self._devtools_is_webhook_logging_enabled():
            return False
        payload_text = self._devtools_format_payload(payload)
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

    def _devtools_is_webhook_logging_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.webhook_log_enabled", default="1"
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    @staticmethod
    def _devtools_format_payload(payload):
        if payload is None:
            return False
        try:
            return json.dumps(payload, ensure_ascii=True, indent=2)
        except (TypeError, ValueError):
            return str(payload)

    def _devtools_outgoing_payload(self, gateway, dto):
        if not dto:
            return {}
        instance = self._instance_name(gateway)
        body = (dto.text or "").strip()
        if body:
            body = self._apply_outgoing_signature(gateway, dto.author_name, body)
        attachments = []
        for attachment in dto.attachments or []:
            attachments.append(
                {
                    "id": attachment.get("id"),
                    "name": attachment.get("name"),
                    "mimetype": attachment.get("mimetype"),
                    "size": attachment.get("size"),
                }
            )
        return {
            "notification_id": dto.notification_id,
            "message_id": dto.message_id,
            "instance": instance,
            "number": dto.chat_id,
            "text": body or False,
            "attachments": attachments,
            "endpoints": self._devtools_outgoing_endpoints(instance, body, attachments),
        }

    @staticmethod
    def _devtools_outgoing_endpoints(instance, body, attachments):
        endpoints = []
        if attachments:
            endpoints.append(f"/message/sendMedia/{instance}")
        if body:
            endpoints.append(f"/message/sendText/{instance}")
        return endpoints

    def _devtools_outgoing_endpoint(self, gateway, dto):
        if not dto:
            return False
        instance = self._instance_name(gateway)
        body = (dto.text or "").strip()
        if body:
            body = self._apply_outgoing_signature(gateway, dto.author_name, body)
        has_attachments = bool(dto.attachments)
        if has_attachments and body:
            return f"/message/sendText/{instance}"
        if has_attachments:
            return f"/message/sendMedia/{instance}"
        if body:
            return f"/message/sendText/{instance}"
        return f"/message/send/{instance}"
