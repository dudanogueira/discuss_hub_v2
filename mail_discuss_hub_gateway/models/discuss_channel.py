# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    _sql_constraints = [
        (
            "discuss_channel_gateway_unique",
            "unique(gateway_id, gateway_channel_token)",
            "Gateway channel token must be unique per gateway.",
        ),
    ]
