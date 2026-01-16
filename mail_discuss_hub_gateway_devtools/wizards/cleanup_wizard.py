# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CleanupWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.cleanup_wizard"
    _description = "Cleanup Discuss/Gateway Data (dev tool)"

    @api.model
    def _get_channel_type_selection(self):
        selection = self.env["discuss.channel"]._fields["channel_type"].selection
        return list(selection) if selection else []

    def _default_channel_type(self):
        selection = self._get_channel_type_selection()
        values = [key for key, _label in selection]
        if "gateway" in values:
            return "gateway"
        if "channel" in values:
            return "channel"
        return values[0] if values else False

    channel_type = fields.Selection(
        selection=_get_channel_type_selection,
        required=True,
        default=_default_channel_type,
        help="Only data related to this channel type will be removed.",
    )
    confirm_cleanup = fields.Boolean(
        string="I understand this will delete data",
        help="Required to run cleanup.",
    )
    confirm_text = fields.Char(
        string='Type "DELETE" to confirm',
        help='Type DELETE to confirm this destructive action.',
    )
    clear_members = fields.Boolean(default=True)
    clear_channels = fields.Boolean(default=True, help="Exclui canais (exceto general).")
    clear_reactions = fields.Boolean(default=True)
    clear_guests = fields.Boolean(default=True)
    clear_messages = fields.Boolean(default=True, help="Somente mensagens de discuss.channel.")

    def action_cleanup(self):
        self.ensure_one()
        if not self.confirm_cleanup:
            raise UserError(_("Please confirm the cleanup checkbox to continue."))
        if (self.confirm_text or "").strip().upper() != "DELETE":
            raise UserError(_('Type "DELETE" to confirm this action.'))

        wizard = self.sudo().with_context(mail_notrack=True, tracking_disable=True)
        env = wizard.env
        Channel = env["discuss.channel"]
        channel_domain = [("channel_type", "=", wizard.channel_type)]
        channels = Channel.search(channel_domain)
        channel_ids = channels.ids

        counts = {}
        if self.clear_members:
            Member = env["discuss.channel.member"]
            member_domain = [("channel_id", "in", channel_ids)]
            counts["members"] = Member.search_count(member_domain)
            Member.search(member_domain).unlink()

        message_ids = []
        if self.clear_reactions or self.clear_messages:
            Message = env["mail.message"]
            msg_domain = [("model", "=", "discuss.channel"), ("res_id", "in", channel_ids)]
            message_ids = Message.search(msg_domain).ids

        if self.clear_reactions:
            Reaction = env["mail.message.reaction"]
            reaction_domain = [("message_id", "in", message_ids)]
            counts["reactions"] = Reaction.search_count(reaction_domain)
            Reaction.search(reaction_domain).unlink()

        if self.clear_guests:
            Guest = env["mail.guest"]
            guest_domain = [("id", "=", 0)]
            gateway_ids = channels.mapped("gateway_id").ids
            tokens = channels.mapped("gateway_channel_token")
            if gateway_ids and tokens:
                guest_domain = [
                    ("gateway_id", "in", gateway_ids),
                    ("gateway_token", "in", tokens),
                ]
            counts["guests"] = Guest.search_count(guest_domain)
            Guest.search(guest_domain).unlink()

        if self.clear_messages:
            Message = env["mail.message"]
            msg_domain = [("id", "in", message_ids)]
            counts["messages"] = Message.search_count(msg_domain)
            Message.search(msg_domain).unlink()

        if self.clear_channels:
            counts["channels"] = len(channel_ids)
            channels.unlink()

        summary = []
        summary.append(_("Channel type: %s") % wizard.channel_type)
        if "members" in counts:
            summary.append(_("Deleted members: %s") % counts["members"])
        if "channels" in counts:
            summary.append(_("Deleted channels: %s") % counts["channels"])
        if "reactions" in counts:
            summary.append(_("Deleted reactions: %s") % counts["reactions"])
        if "guests" in counts:
            summary.append(_("Deleted guests: %s") % counts["guests"])
        if "messages" in counts:
            summary.append(_("Deleted messages: %s") % counts["messages"])

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Cleanup complete"),
                "message": "\n".join(summary) if summary else _("No changes applied."),
                "type": "warning",
                "sticky": False,
            },
        }
