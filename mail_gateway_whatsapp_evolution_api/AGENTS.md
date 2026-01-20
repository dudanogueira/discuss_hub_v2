# AGENTS.md - mail_gateway_whatsapp_evolution_api

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Gateway WhatsApp via Evolution API.

## Dependencias

- `mail_gateway` (OCA).
- `mail_gateway_whatsapp_common` (servico/DTO compartilhado).

## Pontos importantes

- O webhook URL deve ter db fixo no `odoo.conf`.
- Nao usar `?db=` (Evolution API nao preserva querystring).
- Nao adicionar campos em `mail.guest` neste modulo (extensoes devem ficar no common).
- Parseia o payload bruto em `NormalizedPayload` e delega a `mail_gateway_whatsapp_common` para criar/atualizar mensagens.
- Consulte `EVOLUTION_API_REFERENCE.md` para metodos/payloads.
- Divergencias entre doc/modulos/servidor devem ser reconferidas e atualizadas no guia.
- Persistencia de logs de webhook e' controlada pela flag
  `mail_discuss_hub_gateway_devtools.webhook_log_enabled` (Devtools > Recursos)
  e acontece via override de `_receive_update` no devtools, chamando
  `_devtools_log_webhook` quando disponivel.
- Status do webhook: `processed` apenas quando `_process_normalized` retorna `ok` ou `duplicate`;
  caso contrario fica `received` (sem acao no Odoo).

## Arquivos principais

- `models/mail_gateway.py` (campos Evolution e defaults)
- `models/mail_gateway_whatsapp_evolution_api.py` (integra API)
- `views/mail_gateway_evolution.xml`
