# AGENTS.md - mail_gateway_whatsapp_waha

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Gateway WhatsApp via WAHA.

## Dependencias

- `mail_gateway` (OCA).
- `mail_gateway_whatsapp_common` (DTO/servico compartilhado).

## Pontos importantes

- `token` e usado como API key da WAHA (header `X-Api-Key`).
- `waha_api_url` deve ser o base URL (sem barra final).
- `waha_session` default e `default` (WAHA Core suporta apenas esta sessao).
- Webhook inbound ainda nao implementado (somente envio de texto).
- Anexos/medias ainda nao suportados no envio.
