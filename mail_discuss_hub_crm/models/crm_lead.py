# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    discuss_channel_ids = fields.Many2many(
        "discuss.channel",
        "crm_lead_discuss_channel_rel",
        "lead_id",
        "channel_id",
        string="Discuss Sessions",
    )
    discuss_channel_count = fields.Integer(
        compute="_compute_discuss_channel_count",
        string="Discuss Sessions",
    )

    def _compute_discuss_channel_count(self):
        for lead in self:
            lead.discuss_channel_count = len(lead.discuss_channel_ids)

    def action_view_discuss_channels(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "mail.discuss_channel_action_view"
        )
        action["domain"] = [("id", "in", self.discuss_channel_ids.ids)]
        return action
