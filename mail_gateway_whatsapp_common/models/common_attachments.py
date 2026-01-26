import base64
import binascii
import mimetypes

class MailGatewayWhatsappCommonAttachments:
    @staticmethod
    def _attachment_datas_to_base64(attachment):
        payload = attachment.datas
        if isinstance(payload, bytes):
            try:
                payload = payload.decode("utf-8")
            except UnicodeDecodeError:
                payload = False
        if not payload and getattr(attachment, "raw", None):
            payload = base64.b64encode(attachment.raw).decode("ascii")
        if isinstance(payload, str) and payload:
            return payload
        return False


    def _prepare_attachments(self, dto):
        attachments = []
        for attachment in dto.attachments or []:
            if not isinstance(attachment, dict):
                continue
            payload = attachment.get("datas")
            if not payload:
                continue
            decoded = self._decode_attachment_payload(payload)
            if not decoded:
                continue
            mimetype = (attachment.get("mimetype") or "").strip()
            name = self._normalize_attachment_name(
                attachment.get("name"), mimetype, dto
            )
            info = {}
            is_voice = bool(mimetype.startswith("audio/"))
            if not is_voice and dto.message_type:
                is_voice = "audio" in (dto.message_type or "").lower()
            if is_voice:
                info["voice"] = True
            if info:
                attachments.append((name, decoded, info))
            else:
                attachments.append((name, decoded))
        return attachments


    def _decode_attachment_payload(self, payload):
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, bytearray):
            return bytes(payload)
        if isinstance(payload, str):
            payload = payload.strip()
            if not payload:
                return False
            if "base64," in payload:
                payload = payload.split("base64,", 1)[1]
            try:
                return base64.b64decode(payload)
            except (binascii.Error, ValueError):
                return payload.encode("utf-8")
        return False


    def _normalize_attachment_name(self, name, mimetype, dto):
        filename = (name or "").strip()
        if not filename:
            filename = (dto.message_id or "").strip() or "attachment"
        extension = self._guess_attachment_extension(mimetype)
        if extension and "." not in filename:
            filename = f"{filename}{extension}"
        return filename


    def _guess_attachment_extension(self, mimetype):
        if not mimetype:
            return ".bin"
        extension = mimetypes.guess_extension(mimetype)
        return extension or ".bin"
