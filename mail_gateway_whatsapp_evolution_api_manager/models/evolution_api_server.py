# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EvolutionApiServer(models.Model):
    _name = "evolution.api.server"
    _description = "Evolution API Server"
    _order = "name"

    name = fields.Char(required=True)
    base_url = fields.Char(required=True)
    api_key = fields.Char(string="API Key", required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
    instance_ids = fields.One2many(
        "evolution.api.instance",
        "server_id",
        string="Instances",
    )
    instance_count = fields.Integer(compute="_compute_instance_count")

    def _compute_instance_count(self):
        for server in self:
            server.instance_count = len(server.instance_ids)

    def _build_url(self, endpoint):
        base_url = (self.base_url or "").rstrip("/")
        clean_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return f"{base_url}{clean_endpoint}"

    def _api_request(self, method, endpoint, payload=None, api_key=None):
        self.ensure_one()
        token = api_key or self.api_key
        if not self.base_url or not token:
            raise UserError(_("Base URL and API Key are required."))

        url = self._build_url(endpoint)
        headers = {
            "Content-Type": "application/json",
            "apikey": token,
        }
        try:
            response = requests.request(
                method.upper(),
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as exc:
            details = exc.response.text if exc.response else str(exc)
            _logger.error("Evolution API HTTP error (%s): %s", url, details)
            raise UserError(_("Evolution API error: %s") % details)
        except requests.exceptions.RequestException as exc:
            _logger.error("Evolution API connection error (%s): %s", url, exc)
            raise UserError(_("Evolution API connection error: %s") % exc)

    def _normalize_instances_payload(self, payload):
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list):
                return data
        return []

    def _parse_owner_jid(self, owner_jid):
        if not owner_jid or not isinstance(owner_jid, str):
            return False
        return owner_jid.split("@", 1)[0]

    def _safe_json(self, payload):
        try:
            return json.dumps(payload, ensure_ascii=True)
        except Exception:
            return ""

    def action_sync_instances(self):
        self.ensure_one()
        payload = self._api_request("GET", "/instance/fetchInstances")
        items = self._normalize_instances_payload(payload)

        now = fields.Datetime.now()
        existing = {rec.name: rec for rec in self.instance_ids}
        for item in items:
            name = item.get("name") or item.get("instance") or item.get("instanceName")
            if not name:
                continue

            vals = {
                "name": name,
                "connection_status": item.get("connectionStatus") or item.get("status"),
                "profile_name": item.get("profileName"),
                "phone_number": self._parse_owner_jid(item.get("ownerJid")),
                "api_key": item.get("token"),
                "last_sync": now,
            }
            if "raw_payload" in self.env["evolution.api.instance"]._fields:
                vals["raw_payload"] = self._safe_json(item)
            if name in existing:
                instance = existing[name]
                instance.write(vals)
            else:
                vals["server_id"] = self.id
                instance = self.env["evolution.api.instance"].create(vals)

            gateway = instance._find_gateway()
            if gateway:
                if instance.gateway_id != gateway:
                    instance.write({"gateway_id": gateway.id})
            elif instance.gateway_id:
                instance.write({"gateway_id": False})

        return {"type": "ir.actions.client", "tag": "reload"}
