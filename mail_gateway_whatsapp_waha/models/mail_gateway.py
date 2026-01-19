# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import uuid

from odoo import api, fields, models


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
        if not self.env.context.get("skip_waha_defaults"):
            for record in self.filtered(lambda r: r.gateway_type == "whatsapp_waha"):
                updates = {}
                if not record.webhook_key:
                    updates["webhook_key"] = str(uuid.uuid4())
                if not record.waha_session:
                    updates["waha_session"] = "default"
                if updates:
                    record.with_context(skip_waha_defaults=True).write(updates)
        return res
