# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.mail.tools.discuss import Store


class MailMessage(models.Model):
    _inherit = "mail.message"

    def _author_to_store(self, store: Store):
        for message in self:
            data = {
                "author": False,
                "email_from": message.email_from,
            }
            guest_author = message.sudo().author_guest_id.exists()
            if guest_author:
                data["author"] = Store.one(guest_author, fields=["avatar_128", "name"])
            else:
                author = message.sudo().author_id
                if author:
                    data["author"] = Store.one(
                        author, fields=["avatar_128", "is_company", "name", "user"]
                    )
            store.add(message, data)
