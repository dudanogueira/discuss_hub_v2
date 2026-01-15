# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    whatsapp_remote_jid_alt = fields.Char(readonly=True)
    whatsapp_participant_jid = fields.Char(readonly=True)
    whatsapp_is_group = fields.Boolean(
        compute="_compute_whatsapp_is_group",
        store=True,
        readonly=True,
    )

    @api.depends("gateway_channel_token")
    def _compute_whatsapp_is_group(self):
        for channel in self:
            token = channel.gateway_channel_token or ""
            channel.whatsapp_is_group = bool(token.endswith("@g.us"))
