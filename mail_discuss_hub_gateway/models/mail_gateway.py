# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailGateway(models.Model):
    _inherit = "mail.gateway"

    discuss_team_id = fields.Many2one(
        "mail.discuss.team",
        string="Discuss Team",
        check_company=True,
        help="Team that can access channels created by this gateway.",
    )
