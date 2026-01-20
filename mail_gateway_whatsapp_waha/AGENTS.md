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
- Webhook inbound suporta apenas evento `message` (texto).
- `webhook_secret` vira HMAC SHA-256 (`X-Webhook-Hmac`) nos webhooks.
- Common e o unico ponto de conexao com o Odoo; este modulo nao escreve no Odoo.
- Outbound e' roteado pelo common; este modulo so implementa `_send_outbound` (API externa).
- Anexos/medias ainda nao suportados no envio nem no inbound.
- Devtools e opcional e nunca deve ser dependencia de modulo algum.
