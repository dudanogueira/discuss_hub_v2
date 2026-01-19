# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MailGuest(models.Model):
    _inherit = "mail.guest"

    gateway_profile_pic_url = fields.Char()
    # Derived phone token from gateway_token for easy display/search.
    gateway_phone = fields.Char(compute="_compute_gateway_phone")

    @api.depends("gateway_token")
    def _compute_gateway_phone(self):
        for guest in self:
            token = (guest.gateway_token or "").strip()
            if "@" in token:
                token = token.split("@", 1)[0]
            guest.gateway_phone = token or False
