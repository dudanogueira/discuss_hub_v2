# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    discuss_team_id = fields.Many2one(
        "mail.discuss.team",
        string="Discuss Team",
        index=True,
    )
    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        check_company=True,
        index=True,
    )
    assignment_state = fields.Selection(
        [
            ("unassigned", "Unassigned"),
            ("assigned", "Assigned"),
            ("closed", "Closed"),
        ],
        string="Assignment State",
        default="unassigned",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "assigned_user_id" in vals and "assignment_state" not in vals:
                vals["assignment_state"] = (
                    "assigned" if vals.get("assigned_user_id") else "unassigned"
                )
        channels = super().create(vals_list)
        for channel in channels:
            if channel.assigned_user_id:
                channel._ensure_assignee_member(channel.assigned_user_id)
        return channels

    def write(self, vals):
        previous_assignees = {}
        if "assigned_user_id" in vals:
            previous_assignees = {channel.id: channel.assigned_user_id for channel in self}
            if "assignment_state" not in vals:
                vals = dict(vals)
                vals["assignment_state"] = (
                    "assigned" if vals.get("assigned_user_id") else "unassigned"
                )
        result = super().write(vals)
        if "assigned_user_id" in vals:
            for channel in self:
                previous_user = previous_assignees.get(channel.id)
                current_user = channel.assigned_user_id
                if previous_user and previous_user != current_user:
                    channel._remove_assignee_member(previous_user)
                if current_user and current_user != previous_user:
                    channel._ensure_assignee_member(current_user)
        return result

    def _ensure_assignee_member(self, user):
        self.ensure_one()
        if not user or not user.partner_id:
            return
        if self.channel_member_ids.filtered(lambda member: member.partner_id == user.partner_id):
            return
        self.sudo().add_members(
            partner_ids=[user.partner_id.id],
            post_joined_message=False,
        )

    def _remove_assignee_member(self, user):
        self.ensure_one()
        if not user or not user.partner_id:
            return
        members = self.channel_member_ids.filtered(
            lambda member: member.partner_id == user.partner_id
        )
        if members:
            members.sudo().unlink()
