# AGENTS.md - mail_discuss_hub_gateway

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Extensoes do Discuss para gateways (sidebar, logs, autoria de mensagens).

## Dependencias

- `mail_gateway`
- `mail_discuss_hub`

## Arquivos principais

- `models/mail_gateway_webhook_log.py` (logs de webhook)
- `models/mail_guest_manage.py` (manage guest, link com parceiro)
- `static/src/js/gateway_instance_sidebar.esm.js` (categoria por instancia)
- `static/src/js/message_author_fix.esm.js` (autor em mensagens de gateway)
- `views/mail_gateway_webhook_log.xml`
- `views/mail_discuss_hub_gateway_menus.xml`

## Regras

- Nao alterar OCA diretamente.
- Logs e UI devem ficar neste modulo.

