# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MailGateway(models.Model):
    _inherit = "mail.gateway"

    gateway_type = fields.Selection(
        selection_add=[("whatsapp_waha", "WhatsApp (WAHA)")],
        ondelete={"whatsapp_waha": "cascade"},
    )
    waha_api_url = fields.Char(
        string="WAHA API URL",
        help="Base URL of the WAHA server (e.g. https://waha.example.com)",
    )
    waha_session = fields.Char(
        string="WAHA Session",
        default="default",
        help="WAHA session name. WAHA Core supports only 'default'.",
    )
    waha_webhook_event_ids = fields.Many2many(
        "mail.gateway.whatsapp_waha.webhook_event",
        "mail_gateway_whatsapp_waha_event_rel",
        "gateway_id",
        "event_id",
        string="WAHA Webhook Events",
        help=(
            "Events to subscribe in WAHA webhooks. "
            "message/message.any and engine.event(message_create) are processed for now."
        ),
        domain=[("active", "=", True)],
        default=lambda self: self._default_waha_webhook_event_ids(),
    )

    def _get_webhook_url(self):
        """Build webhook URL from base URL to avoid duplicated gateway path."""
        self.ensure_one()
        if self.gateway_type != "whatsapp_waha":
            return super()._get_webhook_url()
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        ).rstrip("/")
        if not base_url or not self.gateway_type or not self.webhook_key:
            return super()._get_webhook_url()
        return f"{base_url}/gateway/{self.gateway_type}/{self.webhook_key}/update"

    @api.model
    def _get_gateway(self, key, state="integrated", gateway_type=False):
        if gateway_type != "whatsapp_waha":
            return super()._get_gateway(key, state=state, gateway_type=gateway_type)
        if not key:
            return False
        record = self.sudo().search(
            [
                ("integrated_webhook_state", "=", state),
                ("gateway_type", "=", gateway_type),
                ("webhook_key", "=", key),
            ],
            limit=1,
        )
        return record._get_gateway_data() if record else False

    def _default_waha_webhook_event_ids(self):
        codes = ["message"]
        return self.env["mail.gateway.whatsapp_waha.webhook_event"].search(
            [("code", "in", codes)]
        ).ids

    def _get_waha_webhook_events(self):
        self.ensure_one()
        if self.gateway_type != "whatsapp_waha":
            return []
        events = self.waha_webhook_event_ids.filtered("active")
        if events:
            return [event.code for event in events]
        default_ids = self._default_waha_webhook_event_ids()
        if default_ids:
            return (
                self.env["mail.gateway.whatsapp_waha.webhook_event"]
                .browse(default_ids)
                .mapped("code")
            )
        return ["message"]

    def _apply_webhook_settings(self):
        self.ensure_one()
        if self.gateway_type != "whatsapp_waha":
            return
        if not self.can_set_webhook or self.integrated_webhook_state != "integrated":
            return
        self.update_webhook()

    def action_select_all_waha_webhook_events(self):
        events = self.env["mail.gateway.whatsapp_waha.webhook_event"].search(
            [("active", "=", True)]
        )
        for record in self.filtered(lambda r: r.gateway_type == "whatsapp_waha"):
            record.waha_webhook_event_ids = [(6, 0, events.ids)]

    def action_clear_waha_webhook_events(self):
        for record in self.filtered(lambda r: r.gateway_type == "whatsapp_waha"):
            record.waha_webhook_event_ids = [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("waha_api_url"):
                vals["waha_api_url"] = vals["waha_api_url"].rstrip("/")
            if vals.get("gateway_type") == "whatsapp_waha":
                if not vals.get("webhook_key"):
                    vals["webhook_key"] = str(uuid.uuid4())
                if not vals.get("waha_session"):
                    vals["waha_session"] = "default"
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("waha_api_url"):
            vals["waha_api_url"] = vals["waha_api_url"].rstrip("/")
        res = super().write(vals)
        webhook_fields = {"waha_webhook_event_ids"}
        if webhook_fields.intersection(vals):
            for record in self.filtered(lambda r: r.gateway_type == "whatsapp_waha"):
                try:
                    record._apply_webhook_settings()
                except UserError as exc:
                    raise UserError(
                        _("Failed to update WAHA webhook: %s") % exc
                    ) from exc
        if not self.env.context.get("skip_waha_defaults"):
            for record in self.filtered(lambda r: r.gateway_type == "whatsapp_waha"):
                updates = {}
                if not record.webhook_key:
                    updates["webhook_key"] = str(uuid.uuid4())
                if not record.waha_session:
                    updates["waha_session"] = "default"
                if not record.waha_webhook_event_ids:
                    default_ids = record._default_waha_webhook_event_ids()
                    if default_ids:
                        updates["waha_webhook_event_ids"] = [(6, 0, default_ids)]
                if updates:
                    record.with_context(skip_waha_defaults=True).write(updates)
        return res
