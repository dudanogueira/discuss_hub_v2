# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    gateway_unread_count = fields.Integer()
