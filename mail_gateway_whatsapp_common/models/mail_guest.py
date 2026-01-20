# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailGuest(models.Model):
    _inherit = "mail.guest"

    gateway_profile_pic_url = fields.Char()
    # Canonical phone identifier used to match guests across gateways.
    gateway_phone = fields.Char(index=True)
