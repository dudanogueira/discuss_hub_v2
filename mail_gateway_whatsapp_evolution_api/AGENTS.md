# AGENTS.md - mail_gateway_whatsapp_evolution_api

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Gateway WhatsApp via Evolution API.

## Dependencias

- `mail_gateway` (OCA).

## Pontos importantes

- O webhook URL deve ter db fixo no `odoo.conf`.
- Nao usar `?db=` (Evolution API nao preserva querystring).
- Consulte `EVOLUTION_API_REFERENCE.md` para metodos/payloads.
- Divergencias entre doc/modulos/servidor devem ser reconferidas e atualizadas no guia.

## Arquivos principais

- `models/mail_gateway.py` (campos Evolution e defaults)
- `models/mail_gateway_whatsapp_evolution_api.py` (integra API)
- `controllers/gateway.py` (webhook receiver)
- `views/mail_gateway_evolution.xml`
