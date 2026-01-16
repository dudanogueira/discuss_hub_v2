# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailGuest(models.Model):
    _inherit = "mail.guest"

    whatsapp_remote_jid = fields.Char(readonly=True)
    whatsapp_remote_jid_alt = fields.Char(readonly=True)
    whatsapp_participant_jid = fields.Char(readonly=True)
    whatsapp_number = fields.Char(readonly=True)
    last_push_name = fields.Char(readonly=True)
    last_seen = fields.Datetime(readonly=True)
