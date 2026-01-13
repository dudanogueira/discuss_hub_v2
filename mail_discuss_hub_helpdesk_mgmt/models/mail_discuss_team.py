# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MailDiscussTeam(models.Model):
    _inherit = "mail.discuss.team"

    helpdesk_team_id = fields.Many2one(
        "helpdesk.ticket.team",
        string="Helpdesk Team",
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        if self.env.context.get("mail_discuss_hub_sync_from_helpdesk"):
            return teams
        for team in teams:
            team._sync_helpdesk_link_and_data(changed_fields=set(team._fields))
        return teams

    def write(self, vals):
        old_links = {team.id: team.helpdesk_team_id for team in self}
        result = super().write(vals)
        if self.env.context.get("mail_discuss_hub_sync_from_helpdesk"):
            return result
        changed_fields = set(vals)
        for team in self:
            team._sync_helpdesk_link_and_data(
                changed_fields=changed_fields,
                previous_helpdesk_team=old_links.get(team.id),
            )
        return result

    def unlink(self):
        if not self.env.context.get("mail_discuss_hub_sync_from_helpdesk"):
            for team in self:
                if team.helpdesk_team_id and team.helpdesk_team_id.discuss_team_id == team:
                    team.helpdesk_team_id.with_context(
                        mail_discuss_hub_sync_from_discuss=True
                    ).write({"discuss_team_id": False})
        return super().unlink()

    def _sync_helpdesk_link_and_data(self, *, changed_fields, previous_helpdesk_team=None):
        self.ensure_one()
        if (
            "helpdesk_team_id" in changed_fields
            and previous_helpdesk_team
            and previous_helpdesk_team != self.helpdesk_team_id
        ):
            if previous_helpdesk_team.discuss_team_id == self:
                previous_helpdesk_team.with_context(
                    mail_discuss_hub_sync_from_discuss=True
                ).write({"discuss_team_id": False})

        if self.helpdesk_team_id and self.helpdesk_team_id.discuss_team_id != self:
            self.helpdesk_team_id.with_context(mail_discuss_hub_sync_from_discuss=True).write(
                {"discuss_team_id": self.id}
            )

        if not self.helpdesk_team_id:
            return

        relevant = {
            "name",
            "active",
            "company_id",
            "user_id",
            "member_ids",
            "color",
            "helpdesk_team_id",
        }
        if not (changed_fields & relevant):
            return

        self.helpdesk_team_id.with_context(mail_discuss_hub_sync_from_discuss=True).write(
            {
                "name": self.name,
                "active": self.active,
                "company_id": self.company_id.id,
                "user_id": self.user_id.id if self.user_id else False,
                "user_ids": [(6, 0, self.member_ids.ids)],
                "color": self.color,
            }
        )

    def _prepare_helpdesk_vals_from_discuss(self, vals):
        mapping = {
            "name": "name",
            "active": "active",
            "company_id": "company_id",
            "user_id": "user_id",
            "member_ids": "user_ids",
            "color": "color",
        }
        result = {}
        for key, target in mapping.items():
            if key in vals:
                result[target] = vals[key]
        return result
