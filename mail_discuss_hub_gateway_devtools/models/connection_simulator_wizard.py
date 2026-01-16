# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import _, fields, models
from odoo.exceptions import UserError


class ConnectionSimulatorWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.connection_simulator_wizard"
    _description = "Connection Simulator (dev tool)"

    gateway_id = fields.Many2one("mail.gateway", string="Gateway", required=True)
    direction = fields.Selection(
        [("in", "Inbound"), ("out", "Outbound")],
        string="Direction",
        default="in",
    )
    event = fields.Selection(
        [
            ("messages.upsert", "Message Upsert"),
            ("send.message", "Send Message"),
            ("message.status", "Message Status"),
            ("message.delete", "Message Delete"),
            ("reaction.upsert", "Reaction Upsert"),
            ("reaction.delete", "Reaction Delete"),
        ],
        string="Event",
        default="messages.upsert",
        required=True,
    )
    chat_id = fields.Char(string="Chat ID", required=True)
    message_id = fields.Char(string="Message ID", required=True)
    from_me = fields.Boolean(string="From Me")
    sender_jid = fields.Char(string="Sender JID")
    sender_name = fields.Char(string="Sender Name")
    text = fields.Text(string="Message Text")
    reaction = fields.Char(string="Reaction")
    reaction_target_id = fields.Char(string="Reaction Target ID")
    status = fields.Char(string="Status")
    process_now = fields.Boolean(string="Process Now", default=True)

    def action_simulate(self):
        self.ensure_one()
        if not self._is_enabled():
            raise UserError(_("Connection simulator is disabled by Devtools settings."))
        if self.gateway_id.gateway_type != "whatsapp_evolution_api":
            raise UserError(_("Connection simulator currently supports Evolution API only."))

        payload = self._build_payload()
        log = self._create_log(payload)
        if self.process_now:
            self._process_payload(payload, log)

        return {
            "type": "ir.actions.act_window",
            "name": _("Webhook Logs"),
            "res_model": "mail.gateway.webhook.log",
            "view_mode": "list,form",
            "target": "current",
            "domain": [("id", "=", log.id)],
        }

    def _build_payload(self):
        timestamp = int(fields.Datetime.now().timestamp())
        key_data = {
            "id": self.message_id,
            "fromMe": bool(self.from_me),
            "remoteJid": self.chat_id,
        }
        if self.sender_jid:
            key_data["participant"] = self.sender_jid
        message = {
            "messageTimestamp": timestamp,
            "messageType": "conversation",
        }
        if self.text:
            message["conversation"] = self.text
        data = {
            "key": key_data,
            "message": message,
            "pushName": self.sender_name or "",
            "timestamp": timestamp,
        }
        if self.reaction:
            data["reaction"] = self.reaction
        if self.reaction_target_id:
            data["reactionMessageId"] = self.reaction_target_id
        if self.status:
            data["status"] = self.status

        return {
            "event": self.event,
            "instance": self.gateway_id.evolution_instance or self.gateway_id.name,
            "data": data,
        }

    def _create_log(self, payload):
        endpoint = self._build_endpoint()
        return (
            self.env["mail.gateway.webhook.log"]
            .sudo()
            .create(
                {
                    "gateway_id": self.gateway_id.id,
                    "direction": self.direction,
                    "status": "received",
                    "event": self.event,
                    "endpoint": endpoint,
                    "http_status": 0,
                    "request_payload": json.dumps(
                        payload, ensure_ascii=True, indent=2, sort_keys=True
                    ),
                }
            )
        )

    def _build_endpoint(self):
        if self.gateway_id.webhook_key:
            return f"/gateway/{self.gateway_id.gateway_type}/{self.gateway_id.webhook_key}/update"
        return f"/gateway/{self.gateway_id.gateway_type}/simulated/update"

    def _process_payload(self, payload, log):
        try:
            event = (payload.get("event") or "").lower()
            normalized_event = event.replace("_", ".")
            gateway_model = self.env["mail.gateway.whatsapp_evolution_api"]
            if normalized_event in {"messages.upsert", "send.message"}:
                gateway_model._receive_update(self.gateway_id, payload)
            else:
                data = payload.get("data") or {}
                chat_token = gateway_model._get_chat_token(data)
                channel = gateway_model._get_channel(self.gateway_id, chat_token, data)
                if channel:
                    gateway_model._refresh_channel_name(channel, data, chat_token)
                dto = gateway_model._build_dto_from_evolution(payload, self.gateway_id, channel)
                if dto:
                    self.env["mail.gateway.whatsapp.common"]._process_normalized(
                        self.gateway_id, dto, channel, author=None
                    )
            log.sudo().write(
                {
                    "status": "processed",
                    "http_status": 200,
                    "response_payload": "processed",
                }
            )
        except Exception as exc:
            log.sudo().write(
                {
                    "status": "error",
                    "http_status": 500,
                    "error_message": str(exc),
                }
            )

    def _is_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.connection_simulator_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")
