# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class MailGateway(models.Model):
    _inherit = "mail.gateway"

    def action_open_evolution_instance(self):
        self.ensure_one()
        if self.gateway_type != "whatsapp_evolution_api":
            raise UserError(_("This gateway is not a WhatsApp Evolution API gateway."))

        instance = self.env["evolution.api.instance"].search(
            [("gateway_id", "=", self.id)],
            limit=1,
        )
        if not instance:
            name = self.evolution_instance or self.name
            if name:
                candidates = self.env["evolution.api.instance"].search(
                    [("name", "=", name), ("company_id", "=", self.company_id.id)]
                )
                if self.evolution_api_url:
                    target_url = (self.evolution_api_url or "").rstrip("/")
                    candidates = candidates.filtered(
                        lambda r: (r.server_id.base_url or "").rstrip("/")
                        == target_url
                    )
                instance = candidates[:1]

        if not instance:
            raise UserError(_("No instance linked to this gateway."))

        action = self.env.ref(
            "mail_gateway_whatsapp_evolution_api_manager.action_evolution_api_instance"
        ).read()[0]
        action.update(
            {
                "res_id": instance.id,
                "view_mode": "form",
                "views": [(False, "form")],
            }
        )
        return action
