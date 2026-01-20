# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    _sql_constraints = [
        (
            "discuss_channel_gateway_unique",
            "unique(gateway_id, gateway_channel_token)",
            "Gateway channel token must be unique per gateway.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if "gateway_id" in self._fields and "discuss_team_id" in self._fields:
            gateway_ids = {
                vals.get("gateway_id")
                for vals in vals_list
                if vals.get("gateway_id") and not vals.get("discuss_team_id")
            }
            if gateway_ids:
                gateways = self.env["mail.gateway"].browse(list(gateway_ids)).sudo()
                gateway_team_map = {
                    gateway.id: gateway.discuss_team_id.id for gateway in gateways
                }
                for vals in vals_list:
                    gateway_id = vals.get("gateway_id")
                    if gateway_id and not vals.get("discuss_team_id"):
                        team_id = gateway_team_map.get(gateway_id)
                        if team_id:
                            vals["discuss_team_id"] = team_id
        return super().create(vals_list)

    def write(self, vals):
        if (
            "gateway_id" in vals
            and "discuss_team_id" not in vals
            and "gateway_id" in self._fields
            and "discuss_team_id" in self._fields
        ):
            gateway = self.env["mail.gateway"].browse(vals["gateway_id"]).sudo()
            vals = dict(vals)
            vals["discuss_team_id"] = gateway.discuss_team_id.id if gateway else False
        return super().write(vals)
