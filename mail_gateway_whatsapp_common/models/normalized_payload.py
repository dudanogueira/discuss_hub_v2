class NormalizedPayload:
    """Lightweight DTO for normalized gateway payloads."""

    _known_fields = (
        "provider",
        "instance",
        "event",
        "message_id",
        "chat_id",
        "from_me",
        "sender_jid",
        "sender_jid_alt",
        "sender_participant_jid",
        "sender_name",
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
