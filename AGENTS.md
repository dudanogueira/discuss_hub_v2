# AGENTS.md - Discuss Hub (Odoo 18)

## Leitura obrigatoria

- Leia este arquivo antes de alterar codigo.
- Leia o `README.rst` e o `AGENTS.md` do modulo que voce vai tocar.
- Procure por outros arquivos .md relevantes (ex: `docs/odoo18-dev-notes.md`).

> Instrucoes de ambiente local (Docker, paths, portas, Traefik) ficam em `AGENTS.local.md`.
> Esse arquivo eh ignorado pelo git.

## Visao geral

Este repositorio adiciona addons locais em `extra-addons/discuss-hub/` para Odoo 18.

Regra principal: **nao alterar OCA/OCB diretamente**. Toda customizacao deve ser feita
nos addons do `discuss-hub` (ou novos addons locais).

## Modulos (mapa rapido)

- `mail_discuss_hub` (core): Settings do Discuss, modelo `mail.discuss.team`, menus.
- `mail_discuss_hub_gateway` (infra Discuss+Gateway): sidebar de instancias, logs, ajustes de autoria.
- `mail_gateway_whatsapp_evolution_api` (gateway): integracao WhatsApp via Evolution API.
- `mail_gateway_whatsapp_evolution_api_manager` (manager): gerencia servidores/instancias Evolution.
- `mail_discuss_hub_crm` (integracao): link + sync bidirecional entre `mail.discuss.team` e `crm.team`.
- `mail_discuss_hub_helpdesk_mgmt` (integracao): link + sync bidirecional entre `mail.discuss.team` e `helpdesk.ticket.team`.

## Regras de trabalho (Odoo 18)

- Views XML: Odoo 18 nao usa `attrs`/`states`.
- Views XML: use `<list>` no lugar de `<tree>`.
- Padrao de entrega: mudanca pequena, upgrade do modulo e reinicio do Odoo.
- Ao sincronizar dados entre modelos, use flags no `context` para evitar loop.

## Guia por addon (o que preservar)

### `mail_discuss_hub`

- Nao colocar regras de integracao aqui; integracoes ficam em addons dedicados.
- `mail.discuss.team`: o `team_leader` (campo `user_id`) deve ser sempre membro.
- Settings: a entrada na sidebar do Settings vem de um `<app>` injetado no form base.

### `mail_discuss_hub_crm` / `mail_discuss_hub_helpdesk_mgmt`

- Integrações sao **link-driven**: nao auto-criar / nao auto-apagar times.
- Sync deve ser bidirecional quando houver link.
- Use flags no `context` para evitar loop:
  - CRM: `mail_discuss_hub_sync_from_crm` / `mail_discuss_hub_sync_from_discuss`
  - Helpdesk: `mail_discuss_hub_sync_from_helpdesk` / `mail_discuss_hub_sync_from_discuss`

### `mail_discuss_hub_gateway`

- Logs de webhook ficam no modelo `mail.gateway.webhook.log`.
- Observacao: o log eh generico, mas so aparece para gateways que escrevem nele.
- Nao mover log para o OCA `mail_gateway`; manter extensoes aqui.

### `mail_gateway_whatsapp_evolution_api`

- Webhook precisa de **db fixo** no `odoo.conf` (Evolution API nao preserva querystring).
- Nao usar `?db=` em webhooks.
- Deduplicacao: use o id externo (Evolution) em `mail.notification.gateway_message_id`.

### `mail_gateway_whatsapp_evolution_api_manager`

- Gerencia servidores/instancias e aplica settings via endpoint da Evolution.
- Nao deve alterar diretamente a logica de gateway (isso fica no addon do gateway).

## Referencias

- Ambiente local e operacao: `AGENTS.local.md` (ignorado)
- Lista de addons: `README.MD`
