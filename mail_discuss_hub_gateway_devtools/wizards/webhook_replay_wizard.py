import json
import time

from odoo import _, fields, models
from odoo.exceptions import UserError


class WebhookReplayWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.webhook_replay_wizard"
    _description = "Replay Webhook Logs (dev tool)"

    direction = fields.Selection(
        [("in", "Inbound"), ("out", "Outbound")],
        default="in",
        required=True,
    )
    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    log_ids = fields.Many2many(
        "mail.gateway.webhook.log",
        "dh_devtools_replay_log_rel",
        "wizard_id",
        "log_id",
        string="Logs",
        help="Opcional: selecione logs especificos para replay.",
    )
    events = fields.Char(
        help="Opcional: lista separada por vírgula de eventos para filtrar (ex: MESSAGES_UPSERT)."
    )
    date_from = fields.Datetime(string="Date from")
    date_to = fields.Datetime(string="Date to")
    limit = fields.Integer(default=0, help="0 para sem limite")
    order = fields.Selection(
        [("asc", "Oldest first"), ("desc", "Newest first")],
        default="asc",
        required=True,
    )
    dry_run = fields.Boolean(default=False, help="Se marcado, apenas relata contagem.")
    report_skipped = fields.Boolean(default=False, help="Relatar logs ignorados.")
    max_report = fields.Integer(default=50, help="Maximo de itens relatados.")
    commit_every = fields.Integer(default=0, help="0 para não commitar parcial.")
    sleep_seconds = fields.Float(default=0.0, help="Delay opcional entre reprocessamentos.")
    update_message_date = fields.Boolean(
        default=True,
        help="Ajusta a data da mensagem criada para a data do webhook.",
    )
    update_create_date = fields.Boolean(
        default=False,
        help="Ajusta create_date da mensagem e relacoes (usa SQL).",
    )

    def action_replay(self):
        self.ensure_one()
        if not self._is_replay_enabled():
            raise UserError(_("Replay is disabled by Devtools settings."))

        logs = self._fetch_logs()
        if self.dry_run:
            return self._notify(
                _("Dry run"),
                _(
                    "Replay would process %s log(s) with direction=%s."
                )
                % (len(logs), self.direction),
            )

        if logs and "internal_routine" in logs._fields:
            logs.sudo().write(
                {
                    "internal_routine": False,
                    "internal_result": False,
                }
            )

        processed = skipped = errors = 0
        reported = 0
        messages = []

        for log in logs:
            payload = self._load_payload(log)
            if payload is None:
                skipped += 1
                if self.report_skipped and reported < self.max_report:
                    messages.append(f"Skipped log {log.id}: invalid payload")
                    reported += 1
                continue

            gateway = self._resolve_gateway(log, payload)
            if not gateway:
                skipped += 1
                if self.report_skipped and reported < self.max_report:
                    messages.append(f"Skipped log {log.id}: gateway not resolved")
                    reported += 1
                continue

            payload = self._normalize_payload(payload)

            dispatcher = (
                self.env[f"mail.gateway.{gateway.gateway_type}"]
                .with_user(gateway.webhook_user_id or self.env.user)
                .with_company(gateway.company_id)
                .with_context(
                    mail_notrack=True,
                    tracking_disable=True,
                    no_gateway_notification=True,
                    gateway_webhook_log_id=log.id,
                )
            )
            try:
                dispatcher._receive_update(gateway, payload)
                processed += 1
            except Exception as exc:  # pylint: disable=broad-except
                errors += 1
                if reported < self.max_report:
                    messages.append(f"Error log {log.id}: {exc}")
                    reported += 1
                continue

            if self.update_message_date:
                self._sync_message_dates(log)
            if self.commit_every and processed % self.commit_every == 0:
                self.env.cr.commit()
            if self.sleep_seconds:
                time.sleep(self.sleep_seconds)

        summary = _("Done: processed=%s skipped=%s errors=%s") % (
            processed,
            skipped,
            errors,
        )
        if messages:
            summary = summary + "\n" + "\n".join(messages)
        return self._notify(_("Replay finished"), summary)

    def _is_replay_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.controlled_replay_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")

    def _fetch_logs(self):
        domain = [("direction", "=", self.direction)]
        if self.log_ids:
            domain.append(("id", "in", self.log_ids.ids))
        if self.events:
            items = [item.strip() for item in self.events.split(",") if item.strip()]
            domain.append(("event", "in", items))
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("create_date", "<=", self.date_to))
        if self.gateway_id:
            domain.append(("gateway_id", "=", self.gateway_id.id))

        order = "create_date asc, id asc" if self.order == "asc" else "create_date desc, id desc"
        logs = self.env["mail.gateway.webhook.log"].sudo().search(domain, order=order)
        if self.limit:
            logs = logs[: self.limit]
        return logs

    def _load_payload(self, log):
        payload_text = log.request_payload or ""
        if not payload_text:
            return None
        try:
            payload = json.loads(payload_text)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    @staticmethod
    def _normalize_payload(payload):
        payload = dict(payload)
        if "event" not in payload:
            payload["event"] = payload.get("event")
        if "data" not in payload:
            payload["data"] = payload.get("data") or {}
        return payload

    def _resolve_gateway(self, log, payload):
        if self.gateway_id:
            return self.gateway_id
        if log.gateway_id:
            return log.gateway_id
        endpoint = log.endpoint or ""
        parts = [part for part in endpoint.split("/") if part]
        usage = token = False
        if "gateway" in parts:
            idx = parts.index("gateway")
            if len(parts) > idx + 2:
                usage = parts[idx + 1]
                token = parts[idx + 2]
        if usage and token:
            gateway = self.env["mail.gateway"].search(
                [("gateway_type", "=", usage), ("webhook_key", "=", token)],
                limit=1,
            )
            if gateway:
                return gateway
        instance_name = self._extract_instance_name(payload)
        if not instance_name:
            return False
        domain = [
            ("gateway_type", "=", "whatsapp_evolution_api"),
            ("evolution_instance", "=", instance_name),
        ]
        server_url = self._extract_server_url(payload)
        gateways = self.env["mail.gateway"].search(domain)
        if server_url:
            server_url = server_url.rstrip("/")
            gateways = gateways.filtered(
                lambda g: (g.evolution_api_url or "").rstrip("/") == server_url
            )
        if gateways:
            return gateways[:1]
        return self.env["mail.gateway"].search(
            [
                ("gateway_type", "=", "whatsapp_evolution_api"),
                ("name", "=", instance_name),
            ],
            limit=1,
        )

    @staticmethod
    def _extract_instance_name(payload):
        for key in ("instance", "instanceName", "instance_name"):
            value = payload.get(key)
            if value:
                return value
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        for key in ("instance", "instanceName", "instance_name"):
            value = data.get(key)
            if value:
                return value
        return False

    @staticmethod
    def _extract_server_url(payload):
        for key in ("server_url", "serverUrl", "serverURL"):
            value = payload.get(key)
            if value:
                return value
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        for key in ("server_url", "serverUrl", "serverURL"):
            value = data.get(key)
            if value:
                return value
        return False

    def _sync_message_dates(self, log):
        if "gateway_webhook_log_id" not in self.env["mail.message"]._fields:
            return
        msg = (
            self.env["mail.message"]
            .sudo()
            .search([("gateway_webhook_log_id", "=", log.id)], order="id desc", limit=1)
        )
        if not msg:
            return
        msg_date = log.create_date
        msg.write({"date": msg_date, "write_date": msg_date})
        if self.update_create_date:
            self.env.cr.execute(
                """
                UPDATE mail_message
                SET create_date=%s
                WHERE id=%s
            """,
                [msg_date, msg.id],
            )
            self.env.cr.execute(
                """
                UPDATE mail_message_res_partner_rel
                SET create_date=%s
                WHERE mail_message_id=%s
            """,
                [msg_date, msg.id],
            )

    @staticmethod
    def _notify(title, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": "info",
                "sticky": False,
            },
        }
