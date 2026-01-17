class NormalizedPayload:
    """Lightweight DTO for normalized gateway payloads."""

    VALID_EVENTS = {
        "message.upsert",
        "message.status",
        "message.delete",
        "reaction.upsert",
        "reaction.delete",
        "contact.update",
        "chat.update",
    }

    _known_fields = (
        "provider",
        "instance",
        "event",
        "message_id",
        "chat_id",
        "chat_name",
        "chat_description",
        "chat_picture_url",
        "chat_unread_count",
        "is_group",
        "from_me",
        "sender_jid",
        "sender_jid_alt",
        "sender_participant_jid",
        "sender_name",
        "contact_jid",
        "contact_name",
        "contact_profile_pic_url",
        "timestamp",
        "message_type",
        "text",
        "caption",
        "attachments",
        "quote_id",
        "quote_text",
        "reaction",
        "reaction_target_id",
        "status",
        "status_raw",
        "raw",
    )

    def __init__(self, **kwargs):
        for field in self._known_fields:
            if field == "from_me":
                value = kwargs.get(field, False)
                value = bool(value) if value is not None else False
            elif field == "is_group":
                value = kwargs.get(field, False)
                value = bool(value) if value is not None else False
            elif field == "chat_unread_count":
                value = kwargs.get(field)
                value = int(value) if value is not None else None
            elif field == "event":
                value = (kwargs.get(field) or "").strip().lower() or None
            elif field == "attachments":
                value = kwargs.get(field) or []
            elif field == "raw":
                value = kwargs.get(field) or {}
            else:
                value = kwargs.get(field)
            setattr(self, field, value)

        for key, value in kwargs.items():
            if key not in self._known_fields:
                setattr(self, key, value)

    def has_attachments(self):
        return bool(self.attachments)

    def to_dict(self):
        data = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            data[key] = value
        return data
