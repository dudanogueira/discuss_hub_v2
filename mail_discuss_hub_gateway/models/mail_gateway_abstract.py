# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models


class MailGatewayAbstract(models.AbstractModel):
    _inherit = "mail.gateway.abstract"

    def _get_channel_vals(self, gateway, token, update):
        author = self._get_author(gateway, update)
        members = []
        auto_users = (
            gateway._get_auto_assign_users()
            if hasattr(gateway, "_get_auto_assign_users")
            else gateway.member_ids
        )
        for user in auto_users:
            if user.partner_id:
                members.append(
                    Command.create(
                        {
                            "partner_id": user.partner_id.id,
                            "unpin_dt": False,
                        }
                    )
                )
        webhook_partner = gateway.webhook_user_id.partner_id if gateway.webhook_user_id else False
        if author and author._name == "res.partner":
            if not webhook_partner or author.id != webhook_partner.id:
                members.append(
                    Command.create(
                        {
                            "partner_id": author.id,
                            "unpin_dt": False,
                        }
                    )
                )
        elif author and author._name == "mail.guest":
            member_model = self.env["discuss.channel.member"]
            if "guest_id" in member_model._fields:
                members.append(Command.create({"guest_id": author.id, "unpin_dt": False}))
        vals = {
            "gateway_channel_token": token,
            "gateway_id": gateway.id,
            "channel_type": "gateway",
            "channel_member_ids": members,
            "company_id": gateway.company_id.id,
        }
        if "group_public_id" in self.env["discuss.channel"]._fields:
            group = gateway._ensure_access_group()
            vals["group_public_id"] = group.id if group else False
        return vals
