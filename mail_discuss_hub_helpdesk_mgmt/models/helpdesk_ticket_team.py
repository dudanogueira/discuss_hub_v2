# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HelpdeskTicketTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    discuss_team_id = fields.Many2one(
        "mail.discuss.team",
        string="Discuss Team",
        copy=False,
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
                if team.discuss_team_id and team.discuss_team_id.helpdesk_team_id == team:
                    team.discuss_team_id.with_context(
                        mail_discuss_hub_sync_from_helpdesk=True
                    ).write({"helpdesk_team_id": False})
        return super().unlink()

    def _sync_discuss_link_and_data(self, *, changed_fields, previous_discuss_team=None):
        self.ensure_one()

        if (
            "discuss_team_id" in changed_fields
            and previous_discuss_team
            and previous_discuss_team != self.discuss_team_id
        ):
            if previous_discuss_team.helpdesk_team_id == self:
                previous_discuss_team.with_context(
                    mail_discuss_hub_sync_from_helpdesk=True
                ).write({"helpdesk_team_id": False})

        if self.discuss_team_id and self.discuss_team_id.helpdesk_team_id != self:
            self.discuss_team_id.with_context(mail_discuss_hub_sync_from_helpdesk=True).write(
                {"helpdesk_team_id": self.id}
            )

        if not self.discuss_team_id:
            return

        relevant = {
            "name",
            "active",
            "company_id",
            "user_id",
            "user_ids",
            "color",
            "discuss_team_id",
        }
        if not (changed_fields & relevant):
            return

        self.discuss_team_id.with_context(mail_discuss_hub_sync_from_helpdesk=True).write(
            {
                "name": self.name,
                "active": self.active,
                "company_id": self.company_id.id,
                "user_id": self.user_id.id if self.user_id else False,
                "member_ids": [(6, 0, self.user_ids.ids)],
                "color": self.color,
            }
        )
