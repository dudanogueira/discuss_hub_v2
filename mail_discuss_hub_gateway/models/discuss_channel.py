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
                if vals.get("gateway_id")
                and (not vals.get("discuss_team_id") or not vals.get("group_public_id"))
            }
            if gateway_ids:
                gateways = self.env["mail.gateway"].browse(list(gateway_ids)).sudo()
                gateway_map = {}
                for gateway in gateways:
                    group_id = (
                        gateway.discuss_team_id.access_group_id.id
                        if gateway.discuss_team_id and gateway.discuss_team_id.access_group_id
                        else False
                    )
                    gateway_map[gateway.id] = {
                        "team_id": gateway.discuss_team_id.id,
                        "group_id": group_id,
                    }
                for vals in vals_list:
                    gateway_id = vals.get("gateway_id")
                    if gateway_id:
                        gateway_info = gateway_map.get(gateway_id) or {}
                        if not vals.get("discuss_team_id") and gateway_info.get("team_id"):
                            vals["discuss_team_id"] = gateway_info["team_id"]
                        if not vals.get("group_public_id") and gateway_info.get("group_id"):
                            vals["group_public_id"] = gateway_info["group_id"]
        return super().create(vals_list)

    def write(self, vals):
        if (
            "gateway_id" in vals
            and "gateway_id" in self._fields
            and "discuss_team_id" in self._fields
        ):
            gateway = self.env["mail.gateway"].browse(vals["gateway_id"]).sudo()
            vals = dict(vals)
            if "discuss_team_id" not in vals:
                vals["discuss_team_id"] = gateway.discuss_team_id.id if gateway else False
            if "group_public_id" not in vals:
                group_id = (
                    gateway.discuss_team_id.access_group_id.id
                    if gateway and gateway.discuss_team_id.access_group_id
                    else False
                )
                vals["group_public_id"] = group_id
        return super().write(vals)
