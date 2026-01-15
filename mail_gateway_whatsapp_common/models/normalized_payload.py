# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""DTO para eventos WhatsApp nao-oficiais.

Providers (Evolution, WAHA, Quepasa, NotificaMe...) constroem este objeto
antes de entregar para o servico comum processar mensagens, reacoes,
citacoes e status.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class NormalizedPayload:
    """Representa um evento de mensagem normalizado.

    Este DTO eh deliberadamente simples para facilitar testes unitarios e
    evolucoes futuras de providers. Campos opcionais podem ser None quando o
    provider nao suportar determinado recurso (ex.: reaction/quote).
    """

    __slots__ = (
        "provider",
        "instance",
        "event",
        "message_id",
        "chat_id",
        "from_me",
        "sender_jid",
        "sender_name",
        "timestamp",
        "message_type",
        "text",
        "caption",
        "mime",
        "filename",
        "media_b64",
        "media_url",
        "attachments",
        "location",
        "contact_vcard",
        "quote_id",
        "quote_text",
        "quote_sender_jid",
        "reaction",
        "reaction_target_id",
        "status",
        "status_raw",
        "errors",
        "raw",
    )

    def __init__(
        self,
        *,
        provider: str,
        instance: Optional[str],
        event: str,
        message_id: Optional[str],
        chat_id: Optional[str],
        from_me: bool = False,
        sender_jid: Optional[str] = None,
        sender_name: Optional[str] = None,
        timestamp: Optional[int] = None,
        message_type: Optional[str] = None,
        text: str = "",
        caption: Optional[str] = None,
        mime: Optional[str] = None,
        filename: Optional[str] = None,
        media_b64: Optional[str] = None,
        media_url: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        location: Optional[Dict[str, Any]] = None,
        contact_vcard: Optional[str] = None,
        quote_id: Optional[str] = None,
        quote_text: Optional[str] = None,
        quote_sender_jid: Optional[str] = None,
        reaction: Optional[str] = None,
        reaction_target_id: Optional[str] = None,
        status: Optional[str] = None,
        status_raw: Optional[str] = None,
        errors: Optional[List[str]] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.provider = provider
        self.instance = instance
        self.event = event
        self.message_id = message_id
        self.chat_id = chat_id
        self.from_me = bool(from_me)
        self.sender_jid = sender_jid
        self.sender_name = sender_name
        self.timestamp = timestamp
        self.message_type = message_type
        self.text = (text or "").strip()
        self.caption = caption
        self.mime = mime
        self.filename = filename
        self.media_b64 = media_b64
        self.media_url = media_url
        self.attachments = attachments or []
        self.location = location
        self.contact_vcard = contact_vcard
        self.quote_id = quote_id
        self.quote_text = quote_text
        self.quote_sender_jid = quote_sender_jid
        self.reaction = reaction
        self.reaction_target_id = reaction_target_id
        self.status = status
        self.status_raw = status_raw
        self.errors = errors or []
        self.raw = raw or {}

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def from_provider(cls, provider: str, payload: Dict[str, Any]) -> "NormalizedPayload":
        """Factory placeholder para adapters implementarem.

        Cada provider deve implementar sua propria classe/metodo construtor
        (ex.: from_evolution, from_waha). Este metodo existe apenas como
        contrato e dispara erro se usado diretamente.
        """

        raise NotImplementedError("Use um construtor especifico do provider")

    # Helpers
    def has_media(self) -> bool:
        return bool(self.media_b64 or self.media_url or self.attachments)

    def has_quote(self) -> bool:
        return bool(self.quote_id)

    def has_reaction(self) -> bool:
        return bool(self.reaction and self.reaction_target_id)

    def has_status(self) -> bool:
        return bool(self.status)
