# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailGuestManage(models.TransientModel):
    _inherit = "mail.guest.manage"

    def _get_partner_vals(self):
        vals = super()._get_partner_vals()
        phone = self._format_phone(self.guest_id.gateway_token)
        if phone and not vals.get("phone") and not vals.get("mobile"):
            vals["mobile"] = phone
        return vals

    def _merge_partner(self, partner):
        self.ensure_one()
        guest = self.guest_id
        gateway = guest.gateway_id
        token = (guest.gateway_token or "").strip()
        related_guests = guest
        if gateway and token:
            related_guests = self.env["mail.guest"].search(
                [
                    ("gateway_id", "=", gateway.id),
                    ("gateway_token", "=", token),
                ]
            )
        if gateway:
            self._ensure_gateway_link(partner, gateway, token)
        self._maybe_set_partner_phone(partner, token)
        for member in self.env["discuss.channel.member"].search(
            [("guest_id", "in", related_guests.ids)]
        ):
            if member.channel_id.channel_member_ids.filtered(
                lambda record, partner=partner: record.partner_id == partner
            ):
                member.unlink()
                continue
            self.env["discuss.channel.member"].create(
                self._channel_member_vals(member, partner)
            )
            member.unlink()
        self.env["mail.message"].search(
            [("author_guest_id", "in", related_guests.ids)]
        ).write(
            {
                "author_id": partner.id,
                "author_guest_id": False,
            }
        )
        if gateway and token:
            self._rename_direct_gateway_channels(partner, gateway, token)

    def _ensure_gateway_link(self, partner, gateway, token):
        link = self.env["res.partner.gateway.channel"].search(
            [("partner_id", "=", partner.id), ("gateway_id", "=", gateway.id)],
            limit=1,
        )
        if link:
            if token and link.gateway_token != token:
                link.sudo().write({"gateway_token": token})
            return
        self.env["res.partner.gateway.channel"].create(
            {
                "name": gateway.name,
                "partner_id": partner.id,
                "gateway_id": gateway.id,
                "gateway_token": token,
            }
        )

    def _maybe_set_partner_phone(self, partner, token):
        phone = self._format_phone(token)
        if not phone:
            return
        if partner.phone or partner.mobile:
            return
        partner.sudo().write({"mobile": phone})

    def _rename_direct_gateway_channels(self, partner, gateway, token):
        channel_name = self._format_channel_name(partner, token)
        if not channel_name:
            return
        channels = self.env["discuss.channel"].search(
            [
                ("gateway_id", "=", gateway.id),
                ("gateway_channel_token", "=", token),
            ]
        )
        channels.sudo().write({"name": channel_name})

    def _format_phone(self, token):
        clean = (token or "").strip()
        if not clean:
            return False
        if clean.startswith("+"):
            clean = clean[1:]
        if not clean.isdigit():
            return False
        return f"+{clean}"

    def _format_channel_name(self, partner, token):
        name = (partner.name or "").strip()
        if name and token:
            return f"{name} <{token}>"
        return name or token
