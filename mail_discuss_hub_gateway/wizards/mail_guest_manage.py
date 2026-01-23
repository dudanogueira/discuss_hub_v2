# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models
from odoo.addons.mail.tools.discuss import Store

_logger = logging.getLogger(__name__)


class MailGuestManage(models.TransientModel):
    _inherit = "mail.guest.manage"

    def _merge_partner(self, partner):
        self._sync_gateway_channels(partner)
        for member in self.env["discuss.channel.member"].search(
            [("guest_id", "=", self.guest_id.id)]
        ):
            self.env["discuss.channel.member"].create(
                self._channel_member_vals(member, partner)
            )
            member.unlink()
        messages = self.env["mail.message"].search(
            [("author_guest_id", "=", self.guest_id.id)]
        )
        if messages:
            messages.write(
                {
                    "author_id": partner.id,
                    "author_guest_id": False,
                }
            )
            messages.invalidate_recordset(["author_id", "author_guest_id"])
            store = Store()
            messages._author_to_store(store)
            self.env.user._bus_send_store(store)

    def _sync_gateway_channels(self, partner):
        guest = self.guest_id
        token = getattr(guest, "gateway_phone", False)
        gateways = self._get_guest_gateways(guest)
        if not gateways:
            return
        if not token:
            _logger.warning(
                "Guest %s has no gateway_phone; skipping gateway partner links.",
                guest.id,
            )
            return
        gateway_channel_model = self.env["res.partner.gateway.channel"]
        for gateway in gateways:
            existing = gateway_channel_model.search(
                [("partner_id", "=", partner.id), ("gateway_id", "=", gateway.id)],
                limit=1,
            )
            if existing:
                if existing.gateway_token != token:
                    existing.write({"gateway_token": token})
                continue
            gateway_channel_model.create(
                {
                    "partner_id": partner.id,
                    "gateway_id": gateway.id,
                    "gateway_token": token,
                }
            )

    def _get_guest_gateways(self, guest):
        members = self.env["discuss.channel.member"].search(
            [("guest_id", "=", guest.id)]
        )
        channels = members.mapped("channel_id")
        channels = channels.filtered(
            lambda channel: channel.channel_type == "gateway" and channel.gateway_id
        )
        return channels.mapped("gateway_id")
