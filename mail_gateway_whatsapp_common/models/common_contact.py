import re

class MailGatewayWhatsappCommonContact:
    def _ensure_guest_member(self, channel, author):
        """Ensure a guest author is a member of the channel."""
        if not channel or not author or author._name != "mail.guest":
            return
        member_model = self.env["discuss.channel.member"].sudo()
        if "guest_id" not in member_model._fields:
            return
        existing = member_model.search(
            [("channel_id", "=", channel.id), ("guest_id", "=", author.id)], limit=1
        )
        if existing:
            return
        member_model.create({"channel_id": channel.id, "guest_id": author.id, "unpin_dt": False})


    def _handle_contact_update(self, gateway, dto, channel, author=None):
        """Sync guest details and optional avatar based on contact updates."""
        contact_jid = (dto.contact_jid or dto.chat_id or "").strip()
        if not contact_jid:
            return {"status": "ignored", "reason": "missing_contact_jid"}
        if dto.is_group:
            return {"status": "ignored", "reason": "group_contact_ignored"}
        if not dto.chat_id:
            dto.chat_id = contact_jid
        guest = self._find_guest_by_phone(dto)
        if not guest:
            if not dto.contact_name:
                return {"status": "ignored", "reason": "guest_not_found"}
            guest = self._get_or_create_guest(gateway, dto)
        if not guest:
            return {"status": "ignored", "reason": "guest_not_found"}
        self._apply_contact_metadata(gateway, dto, channel=channel, guest=guest)
        return {"status": "ok", "guest_id": guest.id}


    def _maybe_enrich_contact_metadata(self, gateway, dto, channel=None, guest=None):
        if not self._should_fetch_contact_metadata(gateway, dto, channel, guest):
            return False
        metadata = self._fetch_contact_metadata(gateway, dto)
        if not metadata:
            return False
        chat_id = (dto.chat_id or "").strip()
        if not chat_id:
            return False
        contact_name = (metadata.get("contact_name") or "").strip()
        contact_pic = (metadata.get("contact_profile_pic_url") or "").strip()
        fallback = self._format_chat_id(chat_id)
        if contact_name and contact_name != fallback:
            dto.contact_name = contact_name
        if contact_pic:
            dto.contact_profile_pic_url = contact_pic
        return True


    def _should_fetch_contact_metadata(self, gateway, dto, channel=None, guest=None):
        if not gateway or not dto:
            return False
        if dto.is_group or not dto.from_me:
            return False
        chat_id = (dto.chat_id or "").strip()
        if not chat_id:
            return False
        contact_name = (dto.contact_name or "").strip()
        fallback = self._format_chat_id(chat_id)
        if contact_name == fallback:
            contact_name = ""
        channel = channel or self._get_channel_by_chat_id(gateway, chat_id)
        guest = guest or self._find_guest_by_phone(dto)
        needs_name = not contact_name
        if needs_name:
            if channel and not self._is_fallback_contact_name(channel.name, chat_id):
                needs_name = False
            if guest and not self._is_fallback_contact_name(guest.name, chat_id):
                needs_name = False
        return needs_name


    def _fetch_contact_metadata(self, gateway, dto):
        provider = self._get_outbound_provider(gateway)
        if provider is False or not hasattr(provider, "_fetch_contact_metadata"):
            return False
        try:
            return provider._fetch_contact_metadata(gateway, dto)
        except Exception:
            self._logger.warning("Failed to fetch contact metadata.", exc_info=True)
            return False


    def _apply_contact_metadata(self, gateway, dto, channel=None, guest=None):
        chat_id = (dto.chat_id or dto.contact_jid or "").strip()
        if not chat_id or self._is_group_chat(chat_id):
            return
        contact_name = (dto.contact_name or "").strip()
        if not contact_name and not dto.from_me:
            contact_name = (dto.sender_name or "").strip()
        contact_pic = (dto.contact_profile_pic_url or "").strip()
        guest = guest or self._find_guest_by_phone(dto)
        if not contact_name and not contact_pic:
            if not guest or self._is_fallback_contact_name(guest.name, chat_id):
                return
        if guest:
            update_vals = {}
            if contact_name and self._should_update_guest_name(guest, contact_name, chat_id):
                update_vals["name"] = contact_name
            if (
                contact_pic
                and "gateway_profile_pic_url" in guest._fields
                and guest.gateway_profile_pic_url != contact_pic
            ):
                update_vals["gateway_profile_pic_url"] = contact_pic
            if update_vals:
                guest.sudo().write(update_vals)
        channel_name = contact_name
        if not channel_name and guest and not self._is_fallback_contact_name(guest.name, chat_id):
            channel_name = (guest.name or "").strip()
        channel = channel or self._get_channel_by_chat_id(gateway, chat_id)
        if channel:
            update_vals = {}
            if channel_name and self._should_update_contact_name(channel.name, channel_name, chat_id):
                update_vals["name"] = channel_name
            if contact_pic and not channel.image_128:
                image_base64 = self._fetch_image_base64(contact_pic)
                if image_base64:
                    update_vals["image_128"] = image_base64
            if update_vals:
                channel.sudo().write(update_vals)


    def _is_fallback_contact_name(self, name, chat_id):
        name = (name or "").strip()
        if not name:
            return True
        fallback = self._format_chat_id(chat_id)
        return name == fallback


    def _should_update_contact_name(self, current_name, contact_name, chat_id):
        contact_name = (contact_name or "").strip()
        if not contact_name:
            return False
        fallback = self._format_chat_id(chat_id)
        if contact_name == fallback:
            return False
        current_name = (current_name or "").strip()
        if not current_name:
            return True
        return current_name == fallback


    def _should_update_guest_name(self, guest, contact_name, chat_id):
        if not guest:
            return False
        if "partner_id" in guest._fields and guest.partner_id:
            return False
        return self._should_update_contact_name(guest.name, contact_name, chat_id)


    def _resolve_author(self, gateway, dto):
        """Resolve the author as a partner (outbound) or guest (inbound)."""
        if dto.from_me:
            user = gateway.webhook_user_id or self.env.user
            return user.partner_id if user else False
        return self._get_or_create_guest(gateway, dto)


    def _get_or_create_guest(self, gateway, dto):
        """Find or create a mail.guest using a canonical phone identifier."""
        token_candidates = self._get_guest_token_candidates(dto)
        phone = self._get_guest_phone(dto, token_candidates=token_candidates)
        if not phone:
            return False
        primary_token = token_candidates[0] if token_candidates else False
        guest_model = self.env["mail.guest"].sudo()
        guest = self._find_guest_by_phone(dto, phone=phone)
        name = self._get_guest_name(dto)
        if guest:
            update_vals = {}
            if name and guest.name != name:
                update_vals["name"] = name
            if primary_token and "gateway_token" in guest._fields:
                if guest.gateway_token != primary_token:
                    update_vals["gateway_token"] = primary_token
            if "gateway_phone" in guest._fields and not guest.gateway_phone:
                update_vals["gateway_phone"] = phone
            if update_vals:
                guest.write(update_vals)
            return guest
        create_vals = {"name": name, "gateway_phone": phone}
        if primary_token and "gateway_token" in guest_model._fields:
            create_vals["gateway_token"] = primary_token
        return guest_model.create(create_vals)


    def _find_guest_by_phone(self, dto, phone=None):
        phone = phone or self._get_guest_phone(dto)
        if not phone:
            return False
        guest_model = self.env["mail.guest"].sudo()
        if "gateway_phone" not in guest_model._fields:
            return False
        return guest_model.search([("gateway_phone", "=", phone)], limit=1)


    def _get_guest_phone(self, dto, token_candidates=None):
        token_candidates = token_candidates or self._get_guest_token_candidates(dto)
        for token in token_candidates:
            phone = self._normalize_phone_token(token)
            if phone:
                return phone
        return False


    def _get_guest_token_candidates(self, dto):
        if dto.is_group:
            candidates = [
                (dto.sender_jid_alt or "").strip(),
                (dto.sender_participant_jid or "").strip(),
                (dto.sender_jid or "").strip(),
            ]
            tokens = [token for token in candidates if token]
            has_phone_jid = any(
                token.endswith("@s.whatsapp.net") or token.endswith("@c.us")
                for token in tokens
            )
            if has_phone_jid:
                tokens = [token for token in tokens if not token.endswith("@lid")]
            return tokens
        if dto.contact_jid:
            return [(dto.contact_jid or "").strip()]
        if dto.chat_id:
            return [(dto.chat_id or "").strip()]
        return []


    def _normalize_phone_token(self, token):
        token = (token or "").strip()
        if not token:
            return False
        if "@" in token:
            token = token.split("@", 1)[0]
        digits = re.sub(r"\D", "", token)
        return digits or False


    def _get_guest_name(self, dto):
        if dto.sender_name:
            return dto.sender_name
        if dto.contact_name:
            return dto.contact_name
        if dto.is_group:
            return self._format_chat_id(dto.sender_participant_jid or dto.sender_jid)
        return self._format_chat_id(dto.chat_id)
