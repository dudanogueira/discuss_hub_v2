# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models


class MailGatewayAbstract(models.AbstractModel):
    _inherit = "mail.gateway.abstract"

    def _get_channel_vals(self, gateway, token, update):
        author = self._get_author(gateway, update)
        members = []
        if author:
            members.append(
                Command.create(
                    {
                        "partner_id": author._name == "res.partner" and author.id,
                        "guest_id": author._name == "mail.guest" and author.id,
                    }
                )
            )
        vals = {
            "gateway_channel_token": token,
            "gateway_id": gateway.id,
            "channel_type": "gateway",
            "channel_member_ids": members,
            "company_id": gateway.company_id.id,
        }
        if "discuss_team_id" in self.env["discuss.channel"]._fields:
            vals["discuss_team_id"] = gateway.discuss_team_id.id or False
        if "group_public_id" in self.env["discuss.channel"]._fields:
            group_id = (
                gateway.discuss_team_id.access_group_id.id
                if gateway.discuss_team_id and gateway.discuss_team_id.access_group_id
                else False
            )
            vals["group_public_id"] = group_id
        return vals
