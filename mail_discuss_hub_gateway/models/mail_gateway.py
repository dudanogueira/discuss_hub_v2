# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailGateway(models.Model):
    _inherit = "mail.gateway"

    discuss_team_id = fields.Many2one(
        "mail.discuss.team",
        string="Discuss Team",
        check_company=True,
        help="Team that can access channels created by this gateway.",
    )

    def write(self, vals):
        result = super().write(vals)
        if "discuss_team_id" in vals:
            channel_model = self.env["discuss.channel"].sudo()
            for gateway in self:
                group_id = (
                    gateway.discuss_team_id.access_group_id.id
                    if gateway.discuss_team_id and gateway.discuss_team_id.access_group_id
                    else False
                )
                channels = channel_model.search([("gateway_id", "=", gateway.id)])
                if channels:
                    channels.write(
                        {
                            "discuss_team_id": gateway.discuss_team_id.id or False,
                            "group_public_id": group_id,
                        }
                    )
        return result
