# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models


class MailGatewayWhatsappCommon(models.AbstractModel):
    _inherit = "mail.gateway.whatsapp.common"

    def _build_outbound_dto(self, gateway, record):
        dto = super()._build_outbound_dto(gateway, record)
        if not dto or not dto.text or not gateway:
            return dto
        if "outgoing_signature" in gateway._fields:
            dto.text = gateway._apply_outgoing_signature(dto.author_name, dto.text)
        return dto

    def _build_channel_members(self, gateway, author):
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
        if author and author._name == "res.partner":
            webhook_partner = gateway.webhook_user_id.partner_id if gateway.webhook_user_id else False
            if not webhook_partner or author.id != webhook_partner.id:
                members.append(Command.create({"partner_id": author.id, "unpin_dt": False}))
        elif author and author._name == "mail.guest":
            member_model = self.env["discuss.channel.member"]
            if "guest_id" in member_model._fields:
                members.append(Command.create({"guest_id": author.id, "unpin_dt": False}))
        return members
