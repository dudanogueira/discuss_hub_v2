# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_discuss_team_groups(self):
        teams = self.env["mail.discuss.team"].sudo().search(
            [("access_group_id", "!=", False)]
        )
        return teams.mapped("access_group_id")

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        groups = users._get_discuss_team_groups()
        if groups:
            group_ids = set(users.mapped("groups_id").ids) & set(groups.ids)
            if group_ids:
                teams = self.env["mail.discuss.team"].sudo().search(
                    [("access_group_id", "in", list(group_ids))]
                )
                teams._sync_members_from_access_group()
        return users

    def write(self, vals):
        groups = None
        before = None
        if "groups_id" in vals:
            groups = self._get_discuss_team_groups()
            if groups:
                group_ids = set(groups.ids)
                before = {
                    user.id: set(user.groups_id.ids) & group_ids for user in self
                }
        res = super().write(vals)
        if "groups_id" in vals and groups:
            group_ids = set(groups.ids)
            changed_group_ids = set()
            for user in self:
                after = set(user.groups_id.ids) & group_ids
                changed_group_ids |= before.get(user.id, set()) ^ after
            if changed_group_ids:
                teams = self.env["mail.discuss.team"].sudo().search(
                    [("access_group_id", "in", list(changed_group_ids))]
                )
                teams._sync_members_from_access_group()
        return res
