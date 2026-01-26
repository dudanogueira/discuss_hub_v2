# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from markupsafe import Markup

from odoo import _, Command, models


class MailGatewayWhatsappCommon(models.AbstractModel):
    _inherit = "mail.gateway.whatsapp.common"

    def _build_outbound_dto(self, gateway, record):
        dto = super()._build_outbound_dto(gateway, record)
        if not dto or not dto.text or not gateway:
            return dto
        if "outgoing_signature" in gateway._fields:
            dto.text = gateway._apply_outgoing_signature(dto.author_name, dto.text)
        return dto

    def _should_reopen_archived(self, gateway):
        return bool(
            gateway
            and "reopen_archived_conversations" in gateway._fields
            and gateway.reopen_archived_conversations
        )

    def _reopen_channel_if_needed(self, gateway, channel, reopened_by=None):
        if not channel or channel.active or not self._should_reopen_archived(gateway):
            return channel
        channel.sudo().action_unarchive()
        if reopened_by:
            notification = Markup('<div class="o_mail_notification">%s</div>') % _(
                "reopened the conversation"
            )
            channel.sudo().message_post(
                author_id=reopened_by.id,
                body=notification,
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )
        return channel

    def _get_or_create_channel(self, gateway, dto, author):
        channel = super()._get_or_create_channel(gateway, dto, author)
        reopened_by = (
            gateway.webhook_user_id.partner_id
            if gateway and gateway.webhook_user_id
            else self.env.user.partner_id
        )
        return self._reopen_channel_if_needed(gateway, channel, reopened_by=reopened_by)

    def _send_outbound(
        self,
        gateway,
        record,
        auto_commit=False,
        raise_exception=False,
        parse_mode=False,
        provider=None,
    ):
        if self._should_reopen_archived(gateway) and hasattr(record, "gateway_channel_id"):
            reopened_by = getattr(record, "author_id", False)
            if not reopened_by and hasattr(record, "mail_message_id"):
                reopened_by = record.mail_message_id.author_id
            if not reopened_by:
                reopened_by = self.env.user.partner_id
            self._reopen_channel_if_needed(
                gateway, record.gateway_channel_id, reopened_by=reopened_by
            )
        return super()._send_outbound(
            gateway,
            record,
            auto_commit=auto_commit,
            raise_exception=raise_exception,
            parse_mode=parse_mode,
            provider=provider,
        )

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
