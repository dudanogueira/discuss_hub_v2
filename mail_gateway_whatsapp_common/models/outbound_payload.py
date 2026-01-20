class OutboundPayload:
    """Lightweight DTO for outbound gateway messages."""

    _known_fields = (
        "provider",
        "gateway_type",
        "instance",
        "notification_id",
        "message_id",
        "chat_id",
        "text",
        "author_name",
        "attachments",
        "raw",
    )

    def __init__(self, **kwargs):
        for field in self._known_fields:
            if field == "attachments":
                value = kwargs.get(field) or []
            elif field == "text":
                value = kwargs.get(field) or ""
            elif field == "raw":
                value = kwargs.get(field) or {}
            else:
                value = kwargs.get(field)
            setattr(self, field, value)

        for key, value in kwargs.items():
            if key not in self._known_fields:
                setattr(self, key, value)

    def has_text(self):
        return bool((self.text or "").strip())

    def has_attachments(self):
        return bool(self.attachments)

    def to_dict(self):
        data = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            data[key] = value
        return data
