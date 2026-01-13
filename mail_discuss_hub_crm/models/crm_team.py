# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    discuss_team_id = fields.Many2one(
        "mail.discuss.team",
        string="Discuss Team",
    )

    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        if self.env.context.get("mail_discuss_hub_sync_from_discuss"):
            return teams
        for team in teams:
            team._sync_discuss_link_and_data(changed_fields=set(team._fields))
        return teams

    def write(self, vals):
        old_links = {team.id: team.discuss_team_id for team in self}
        result = super().write(vals)
        if self.env.context.get("mail_discuss_hub_sync_from_discuss"):
            return result
        changed_fields = set(vals)
        for team in self:
            team._sync_discuss_link_and_data(
                changed_fields=changed_fields,
                previous_discuss_team=old_links.get(team.id),
            )
        return result

    def unlink(self):
        if not self.env.context.get("mail_discuss_hub_sync_from_discuss"):
            for team in self:
                if team.discuss_team_id and team.discuss_team_id.crm_team_id == team:
                    team.discuss_team_id.with_context(
                        mail_discuss_hub_sync_from_crm=True
                    ).write({"crm_team_id": False})
        return super().unlink()

    def _sync_discuss_link_and_data(self, *, changed_fields, previous_discuss_team=None):
        self.ensure_one()
        if (
            "discuss_team_id" in changed_fields
            and previous_discuss_team
            and previous_discuss_team != self.discuss_team_id
        ):
            if previous_discuss_team.crm_team_id == self:
                previous_discuss_team.with_context(mail_discuss_hub_sync_from_crm=True).write(
                    {"crm_team_id": False}
                )

        if self.discuss_team_id and self.discuss_team_id.crm_team_id != self:
            self.discuss_team_id.with_context(mail_discuss_hub_sync_from_crm=True).write(
                {"crm_team_id": self.id}
            )

        if not self.discuss_team_id:
            return

        relevant = {
            "name",
            "active",
            "company_id",
            "user_id",
            "member_ids",
            "color",
            "discuss_team_id",
        }
        if not (changed_fields & relevant):
            return

        member_ids = self.member_ids
        if self.user_id:
            member_ids |= self.user_id
        self.discuss_team_id.with_context(mail_discuss_hub_sync_from_crm=True).write(
            {
                "name": self.name,
                "active": self.active,
                "company_id": self.company_id.id,
                "user_id": self.user_id.id if self.user_id else False,
                "member_ids": [(6, 0, member_ids.ids)],
                "color": self.color,
            }
        )

    def _prepare_discuss_vals_from_crm(self, vals):
        mapping = {
            "name": "name",
            "active": "active",
            "company_id": "company_id",
            "user_id": "user_id",
            "member_ids": "member_ids",
            "color": "color",
        }
        result = {}
        for key, target in mapping.items():
            if key in vals:
                result[target] = vals[key]
        return result
