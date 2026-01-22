# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    _sql_constraints = [
        (
            "group_public_id_check",
            "CHECK (channel_type in ('channel', 'gateway') OR group_public_id IS NULL)",
            "Group authorization is only supported on channels and gateway channels.",
        ),
    ]

    discuss_team_id = fields.Many2one(
        "mail.discuss.team",
        string="Discuss Team",
        index=True,
    )

    @api.constrains("group_public_id", "group_ids")
    def _constraint_group_id_channel(self):
        auto_subscribe_blocked = self.sudo().filtered(
            lambda channel: channel.channel_type != "channel" and channel.group_ids
        )
        if auto_subscribe_blocked:
            raise ValidationError(
                _("Group auto-subscription is only supported on channels.")
            )
        unauthorized_channels = self.sudo().filtered(
            lambda channel: channel.channel_type not in ("channel", "gateway")
            and channel.group_public_id
        )
        if unauthorized_channels:
            raise ValidationError(
                _("Group authorization is only supported on channels and gateway channels.")
            )

    def _channel_basic_info(self):
        info = super()._channel_basic_info()
        info["active"] = self.active
        return info
