# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MailDiscussTeam(models.Model):
    _inherit = "mail.discuss.team"

    crm_team_id = fields.Many2one(
        "crm.team",
        string="CRM Team",
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        if self.env.context.get("mail_discuss_hub_sync_from_crm"):
            return teams
        for team in teams:
            team._sync_crm_link_and_data(changed_fields=set(team._fields))
        return teams

    def write(self, vals):
        old_links = {team.id: team.crm_team_id for team in self}
        result = super().write(vals)
        if self.env.context.get("mail_discuss_hub_sync_from_crm"):
            return result
        changed_fields = set(vals)
        for team in self:
            team._sync_crm_link_and_data(
                changed_fields=changed_fields,
                previous_crm_team=old_links.get(team.id),
            )
        return result

    def unlink(self):
        if not self.env.context.get("mail_discuss_hub_sync_from_crm"):
            for team in self:
                if team.crm_team_id and team.crm_team_id.discuss_team_id == team:
                    team.crm_team_id.with_context(
                        mail_discuss_hub_sync_from_discuss=True
                    ).write({"discuss_team_id": False})
        return super().unlink()

    def _sync_crm_link_and_data(self, *, changed_fields, previous_crm_team=None):
        self.ensure_one()
        if "crm_team_id" in changed_fields and previous_crm_team and previous_crm_team != self.crm_team_id:
            if previous_crm_team.discuss_team_id == self:
                previous_crm_team.with_context(mail_discuss_hub_sync_from_discuss=True).write(
                    {"discuss_team_id": False}
                )

        if self.crm_team_id and self.crm_team_id.discuss_team_id != self:
            self.crm_team_id.with_context(mail_discuss_hub_sync_from_discuss=True).write(
                {"discuss_team_id": self.id}
            )

        if not self.crm_team_id:
            return

        relevant = {
            "name",
            "active",
            "company_id",
            "user_id",
            "member_ids",
            "color",
            "crm_team_id",
        }
        if not (changed_fields & relevant):
            return

        self.crm_team_id.with_context(mail_discuss_hub_sync_from_discuss=True).write(
            {
                "name": self.name,
                "active": self.active,
                "company_id": self.company_id.id,
                "user_id": self.user_id.id if self.user_id else False,
                "member_ids": [(6, 0, self.member_ids.ids)],
                "color": self.color,
            }
        )

    def _prepare_crm_vals_from_discuss(self, vals):
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
