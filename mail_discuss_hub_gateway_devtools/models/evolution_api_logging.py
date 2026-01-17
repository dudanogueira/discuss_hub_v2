# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import models
from odoo.tools import html2plaintext


class MailGatewayWhatsappEvolutionApi(models.AbstractModel):
    _inherit = "mail.gateway.whatsapp_evolution_api"

    def _send(
        self,
        gateway,
        record,
        auto_commit=False,
        raise_exception=False,
        parse_mode=False,
    ):
        log_record = self._devtools_log_webhook(
            gateway,
            direction="out",
            status="sending",
            event="message.send",
            endpoint=self._devtools_outgoing_endpoint(gateway, record),
            payload=self._devtools_outgoing_payload(gateway, record),
        )
        if log_record:
            log_record.sudo().write(
                {
                    "internal_routine": "send_message",
                    "internal_result": "received",
                }
            )
        try:
            res = super()._send(
                gateway,
                record,
                auto_commit=auto_commit,
                raise_exception=raise_exception,
                parse_mode=parse_mode,
            )
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
            if record.notification_status == "sent":
                log_record.sudo().write(
                    {
                        "status": "sent",
                        "internal_result": "processed",
                    }
                )
            elif record.notification_status == "exception":
                log_record.sudo().write(
                    {
                        "status": "error",
                        "error_message": record.failure_reason,
                        "internal_result": "received",
                    }
                )
        return res

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

    def _devtools_outgoing_payload(self, gateway, record):
        channel = record.gateway_channel_id
        if not channel:
            return {"notification_id": record.id, "message_id": record.mail_message_id.id}
        instance = self._instance_name(gateway)
        body = html2plaintext(self._get_message_body(record) or "")
        if body:
            body = self._apply_outgoing_signature(gateway, record, body)
        attachments = []
        for attachment in record.mail_message_id.attachment_ids:
            attachments.append(
                {
                    "id": attachment.id,
                    "name": attachment.name,
                    "mimetype": attachment.mimetype,
                    "size": attachment.file_size,
                }
            )
        return {
            "notification_id": record.id,
            "message_id": record.mail_message_id.id,
            "instance": instance,
            "number": channel.gateway_channel_token,
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

    def _devtools_outgoing_endpoint(self, gateway, record):
        instance = self._instance_name(gateway)
        body = html2plaintext(self._get_message_body(record) or "")
        if body:
            body = self._apply_outgoing_signature(gateway, record, body)
        has_attachments = bool(record.mail_message_id.attachment_ids)
        if has_attachments and body:
            return f"/message/sendText/{instance}"
        if has_attachments:
            return f"/message/sendMedia/{instance}"
        if body:
            return f"/message/sendText/{instance}"
        return f"/message/send/{instance}"
