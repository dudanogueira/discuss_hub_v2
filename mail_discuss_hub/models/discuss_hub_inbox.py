# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DiscussHubInbox(models.Model):
    _name = "discuss.hub.inbox"
    _description = "Discuss Hub Inbox"
    _order = "name"

    name = fields.Char(required=True)
    inbox_type = fields.Selection(
        [],
        required=False,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company.id,
    )
