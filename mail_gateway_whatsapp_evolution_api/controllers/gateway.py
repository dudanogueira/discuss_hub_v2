# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from odoo import SUPERUSER_ID, api, http
from odoo.http import request
from odoo.modules.registry import Registry

from odoo.addons.mail_gateway.controllers.gateway import (
    GatewayController as BaseGatewayController,
)

_logger = logging.getLogger(__name__)


class GatewayController(BaseGatewayController):
    @http.route(
        "/gateway/<string:usage>/<string:token>/update",
        type="http",
        auth="none",
        methods=["GET", "POST"],
        csrf=False,
    )
    def post_update(self, usage, token, *args, **kwargs):
        env, cr, manual_env = self._get_env()
        if not env:
            return self._empty_response()
        if manual_env:
            request.env = env
            request.db = env.cr.dbname
        try:
            if request.httprequest.method == "GET":
                return self._handle_get(env, usage, token, **kwargs)
            response = self._handle_post(env, usage, token)
            if manual_env:
                cr.commit()
            return response
        except Exception:
            if manual_env and cr:
                cr.rollback()
            raise
        finally:
            if manual_env and cr:
                cr.close()

    def _get_env(self):
        if request.env and request.env.uid:
            return request.env, None, False
        dbname = request.db or request.params.get("db")
        if dbname:
            dbname = dbname.strip()
        if not dbname or dbname not in http.db_filter([dbname]):
            _logger.warning("Gateway webhook without valid db param")
            return None, None, False
        registry = Registry(dbname)
        cr = registry.cursor()
        env = api.Environment(cr, SUPERUSER_ID, {})
        return env, cr, True

    def _handle_get(self, env, usage, token, **kwargs):
        bot_data = env["mail.gateway"]._get_gateway(
            token, gateway_type=usage, state="pending"
        )
        if not bot_data:
            return self._empty_response()
        dispatcher = (
            env[f"mail.gateway.{usage}"]
            .with_user(bot_data["webhook_user_id"])
            .with_company(bot_data["company_id"])
        )
        return dispatcher._receive_get_update(bot_data, request, **kwargs)

    def _handle_post(self, env, usage, token):
        bot_data = env["mail.gateway"]._get_gateway(
            token, gateway_type=usage, state="integrated"
        )
        if not bot_data:
            _logger.warning("Gateway not found for token %s with usage %s", token, usage)
            return self._empty_response()
        payload = request.httprequest.get_data()
        charset = request.httprequest.mimetype_params.get("charset") or "utf-8"
        try:
            jsonrequest = json.loads(payload.decode(charset))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _logger.warning("Invalid JSON payload received on gateway webhook")
            return self._empty_response()
        gateway = env["mail.gateway"].browse(bot_data["id"])
        log_record = self._create_webhook_log(
            env,
            gateway,
            direction="in",
            status="received",
            event=jsonrequest.get("event"),
            endpoint=request.httprequest.path,
            payload=jsonrequest,
        )
        dispatcher = (
            env[f"mail.gateway.{usage}"]
            .with_user(bot_data["webhook_user_id"])
            .with_context(
                no_gateway_notification=True,
                gateway_webhook_log_id=log_record.id if log_record else False,
            )
        )
        if not dispatcher._verify_update(bot_data, jsonrequest):
            _logger.warning(
                "Message could not be verified for token %s with usage %s",
                token,
                usage,
            )
            if log_record:
                log_record.sudo().write({"status": "rejected"})
            return self._empty_response()
        try:
            dispatcher._receive_update(gateway, jsonrequest)
        except Exception as exc:
            if log_record:
                log_record.sudo().write(
                    {"status": "error", "error_message": str(exc)}
                )
            raise
        if log_record:
            log_record.sudo().write({"status": "processed"})
        return self._empty_response()

    def _empty_response(self):
        return request.make_response(
            json.dumps({}),
            [
                ("Content-Type", "application/json"),
            ],
        )

    def _create_webhook_log(
        self,
        env,
        gateway,
        direction,
        status,
        payload=None,
        event=None,
        endpoint=None,
    ):
        if "mail.gateway.webhook.log" not in env:
            return False
        if not self._is_webhook_logging_enabled(env):
            return False
        payload_text = self._format_payload(payload)
        return (
            env["mail.gateway.webhook.log"]
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

    def _is_webhook_logging_enabled(self, env):
        param = (
            env["ir.config_parameter"]
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
