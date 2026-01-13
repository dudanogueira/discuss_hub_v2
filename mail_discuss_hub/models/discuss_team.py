# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MailDiscussTeam(models.Model):
    _name = "mail.discuss.team"
    _description = "Discuss Team"
    _order = "sequence, name"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Team Leader",
        check_company=True,
    )
    member_ids = fields.Many2many(
        "res.users",
        string="Members",
    )
    color = fields.Integer(default=0)
    description = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        teams._ensure_team_leader_in_members()
        return teams

    def write(self, vals):
        result = super().write(vals)
        if "user_id" in vals or "member_ids" in vals:
            self._ensure_team_leader_in_members()
        return result

    def _ensure_team_leader_in_members(self):
        for team in self:
            if team.user_id and team.user_id not in team.member_ids:
                team.sudo().write({"member_ids": [(4, team.user_id.id)]})
