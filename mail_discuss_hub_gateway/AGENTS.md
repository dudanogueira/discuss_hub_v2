# AGENTS.md - mail_discuss_hub_gateway

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Extensoes do Discuss para gateways (sidebar, autoria de mensagens).

## Dependencias

- `mail_gateway`
- `mail_discuss_hub`

## Arquivos principais

- `models/mail_guest_manage.py` (manage guest, link com parceiro)
- `static/src/js/gateway_instance_sidebar.esm.js` (categoria por instancia)
- `static/src/js/message_author_fix.esm.js` (autor em mensagens de gateway)
- `views/mail_discuss_hub_gateway_menus.xml`

## Regras

- Nao alterar OCA diretamente.
- Logging de webhook eh opcional e fornecido por `mail_discuss_hub_devtools` (modelo e UI).
