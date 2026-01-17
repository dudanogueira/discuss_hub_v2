# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailGatewayWhatsappEvolutionApiMixin(models.AbstractModel):
    _name = "mail.gateway.whatsapp_evolution_api.mixin"
    _description = "Evolution API helper"

    def _evolution_api_join_url(self, base_url, endpoint):
        base_url = (base_url or "").rstrip("/")
        clean_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return f"{base_url}{clean_endpoint}"

    def _evolution_api_request(
        self,
        base_url,
        api_key,
        method,
        endpoint,
        payload=None,
        log_record=None,
    ):
        if not base_url or not api_key:
            raise UserError(_("Evolution API base URL and API key are required."))
        # Keep method/payload aligned with EVOLUTION_API_REFERENCE.md.
        url = self._evolution_api_join_url(base_url, endpoint)
        headers = {
            "Content-Type": "application/json",
            "apikey": api_key,
        }
        hint = ""
        if "/manager" in (base_url or ""):
            hint = _(" Check the Base URL (use the API root, without /manager).")
        try:
            response = requests.request(
                method.upper(),
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            if log_record:
                log_record.sudo().write(
                    {
                        "status": "sent",
                        "http_status": response.status_code,
                        "response_payload": response.text,
                    }
                )
            response.raise_for_status()
            if not response.content:
                return {}
            try:
                return response.json()
            except ValueError:
                snippet = response.text[:500] if response.text else ""
                details = _("Invalid JSON response (status %s).") % response.status_code
                if snippet:
                    details = f"{details} {snippet}"
                _logger.error("Evolution API invalid JSON (%s): %s", url, details)
                if log_record:
                    log_record.sudo().write(
                        {
                            "status": "error",
                            "error_message": details,
                        }
                    )
                raise UserError(_("Evolution API error: %s") % f"{details}{hint}")
        except requests.exceptions.HTTPError as exc:
            details = exc.response.text if exc.response else str(exc)
            _logger.error("Evolution API HTTP error (%s): %s", url, details)
            if log_record:
                log_record.sudo().write(
                    {
                        "status": "error",
                        "error_message": details,
                    }
                )
            raise UserError(_("Evolution API error: %s") % details)
        except requests.exceptions.RequestException as exc:
            _logger.error("Evolution API connection error (%s): %s", url, exc)
            if log_record:
                log_record.sudo().write(
                    {
                        "status": "error",
                        "error_message": str(exc),
                    }
                )
            raise UserError(_("Evolution API connection error: %s") % exc)

    def _evolution_api_set_settings(self, base_url, api_key, instance_name, payload):
        if not instance_name:
            raise UserError(_("Evolution API instance name is required."))
        # Payload must match the server schema (see EVOLUTION_API_REFERENCE.md).
        return self._evolution_api_request(
            base_url,
            api_key,
            "POST",
            f"/settings/set/{instance_name}",
            payload=payload,
        )
