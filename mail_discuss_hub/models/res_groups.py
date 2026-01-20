# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    @api.model_create_multi
    def create(self, vals_list):
        groups = super().create(vals_list)
        groups._sync_discuss_team_members()
        return groups

    def write(self, vals):
        res = super().write(vals)
        if "users" in vals:
            self._sync_discuss_team_members()
        return res

    def _sync_discuss_team_members(self):
        if self.env.context.get("mail_discuss_hub_skip_group_sync"):
            return
        teams = self.env["mail.discuss.team"].sudo().search(
            [("access_group_id", "in", self.ids)]
        )
        if teams:
            teams._sync_members_from_access_group()
