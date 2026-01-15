# AGENTS.md - mail_gateway_whatsapp_common

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Camada comum para gateways WhatsApp nao-oficiais:
- DTO `NormalizedPayload`.
- Servico `_process_normalized` para message/status/delete/reaction.
- Campos em `mail.message` para id externo, chat, status, quote, reactions e payload bruto.

## Dependencias

- `mail_gateway` (OCA).

## Regras

- Providers (Evolution, WAHA, Quepasa, NotificaMe...) devem apenas converter o webhook bruto para `NormalizedPayload` e chamar o servico comum.
- Idempotencia: usar `(gateway_id, gateway_remote_id)`.
- Evitar fallbacks legados; projeto greenfield.
