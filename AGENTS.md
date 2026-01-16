# AGENTS.md - Discuss Hub (Odoo 18)

## Leitura obrigatoria

- Leia este arquivo antes de alterar codigo.
- Leia o `README.rst` e o `AGENTS.md` do modulo que voce vai tocar.
- Procure por outros arquivos .md relevantes.
- Sempre que descobrir algo importante (regra, endpoint, bug ou fluxo), atualize este arquivo.
- Regra operacional: sempre que modificar codigo, rode o upgrade do(s) modulo(s) tocado(s) e reinicie os containers (Odoo e banco, conforme rotina local).

## Visao geral

Este repositorio adiciona addons locais em `extra-addons/discuss-hub/` para Odoo 18.

Regra principal: **nao alterar OCA/OCB diretamente**. Toda customizacao deve ser feita
nos addons do `discuss-hub` (ou novos addons locais).

## Modulos (mapa rapido)

- `mail_discuss_hub` (core): Settings do Discuss, modelo `mail.discuss.team`, menus.
- Integracoes: `mail_discuss_hub_crm`, `mail_discuss_hub_helpdesk_mgmt` (e futuros) dependem apenas do core + modulo alvo.
- `mail_discuss_hub_gateway` (infra Discuss+Gateway): sidebar de instancias, ajustes de autoria (sem logging obrigatorio).
- `mail_discuss_hub_gateway_devtools` (dev): modelo/log de webhook e utilidades opcionais (views, replay, cleanup). Nao deve ser dependencia de producao.
- `mail_gateway_whatsapp_common` (gateway core WhatsApp): DTO/servico unificado para mensagens/status/reactions.
- `mail_gateway_whatsapp_evolution_api` (provider): integra Evolution API, delega processamento ao common.
- `mail_gateway_whatsapp_evolution_api_manager` (manager): gerencia servidores/instancias Evolution.

## Regras de trabalho (Odoo 18)

- Views XML: Odoo 18 nao usa `attrs`/`states`.
- Views XML: use `<list>` no lugar de `<tree>`.
- Padrao de entrega: mudanca pequena, upgrade do modulo e reinicio do Odoo.
- Sempre que modificar codigo, rode a atualizacao do modulo e reinicie os containers (banco e Odoo).
- Ao sincronizar dados entre modelos, use flags no `context` para evitar loop.
- Se houver divergencia entre doc e comportamento real, confronte com outra fonte
  (servidor, modulos de referencia, ou teste local) e atualize `EVOLUTION_API_REFERENCE.md`.
- Projeto greenfield: evite fallbacks e legados sem comprovacao; prefira fluxos diretos e dados canonicos.

## Ambiente local (unico arquivo)

Este repositorio roda Odoo 18 (OCB) via Docker em `/home/administrador/odoo18`.

### Subir

```bash
cd /home/administrador/odoo18
# se nao existir .env:
# cp .env.example .env
# edite o .env (POSTGRES_PASSWORD e ODOO_ADMIN_PASSWORD)
docker compose up -d --build
```

### Containers / Bancos (exemplo)

- Odoo principal (db `odoo`) roda no service `odoo`.

> Ajuste os nomes acima de acordo com o seu `docker-compose.yml`.

### Acessar

- Local/IP: `http://127.0.0.1:8070` (ou `http://<ip>:8070`)
- Via Traefik (se habilitado): configure `TRAEFIK_ENABLE=true` e `TRAEFIK_HOST` no `.env`.

Na primeira abertura, crie a base pelo wizard do Odoo. A "master password" eh
`ODOO_ADMIN_PASSWORD` do `.env`.

### Logs e status

```bash
cd /home/administrador/odoo18
docker compose ps
docker compose logs -f --tail=200 odoo
```

### Rotina: upgrade / install de modulos (db principal)

```bash
cd /home/administrador/odoo18

# Upgrade
docker compose exec -T odoo /opt/venv/bin/python /opt/odoo/odoo-bin \
  -c /etc/odoo/odoo.conf -d odoo -u modulo --stop-after-init

# Install
docker compose exec -T odoo /opt/venv/bin/python /opt/odoo/odoo-bin \
  -c /etc/odoo/odoo.conf -d odoo -i modulo --stop-after-init

# Reinicio do Odoo
docker compose restart odoo
```

### Notas locais

- Base URL (Odoo): `Settings > Technical > Parameters > System Parameters` (`web.base.url`).
- DNS / IP / TLS: anote aqui as particularidades do seu host.

## Development notes (Odoo 17+)

- `attrs` e `states` nao sao suportados nas views. Use atributos diretos:
  - `invisible="condition"`
  - `readonly="condition"`
  - `required="condition"`
- Condicoes seguem o mesmo estilo de expressoes de atributos:
  - `invisible="gateway_type != 'whatsapp_evolution_api'"`
  - `invisible="not field_name or state == 'draft'"`
- Em listas, use `column_invisible="condition"` quando precisar controlar colunas.

## Insight: aba "Privacidade" em `discuss.channel` (Odoo core)

- Origem: padrao do Odoo (OCB), addon `mail`, view `mail.discuss_channel_view_form`.
- Campos importantes para desenho futuro de routing/inbox:
  - `group_public_id` (Authorized Group): grupo autorizado para canais do tipo `channel`.
    - Restricoes: so para `channel_type='channel'`; nao pode em sub-canais (`parent_channel_id`).
    - Efeitos: restringe autocomplete de convite e influencia sugestoes de @mention (considera canal pai).
    - Potencial: pode servir como metadado padrao de "escopo" (ex.: time) sem inventar UI nova.
  - `group_ids` (Auto Subscribe Groups): auto-adiciona membros via grupos.
    - Cuidado: para inbox-style (Chatwoot-like), tende a ir contra o principio de nao inflar membership.

Recomendacao para inbox/routing
- Considerar mapear `mail.discuss.team` -> `res.groups` e usar `group_public_id` como sinalizador de privacidade/escopo.
- Manter visibilidade por time via record rules (read por time) separada do membership (nao depender de `group_ids`).

## Gateway routing (mail_gateway)

- Webhook URL: `/gateway/<usage>/<webhook_key>/update`
- `usage` eh o tipo de gateway (`whatsapp_evolution_api` neste projeto).
- `webhook_key` eh a chave publica na URL; `webhook_secret` eh o header opcional
  para validacao.
- Para Evolution API, nao use `?db=` na URL do webhook (a API nao preserva a querystring).
  O database deve ser fixo no `odoo.conf`.

## Evolution API references (repo)

Use estes arquivos como referencia de payloads e endpoints:
- `extra-addons-reference/discuss_hub_legacy/discuss_hub/models/plugins/evolution.py`
- `extra-addons-reference/wa_conn_apps/wa_conn_evolution/models/wa_account_evolution.py`
- `extra-addons-reference/odoo-whatsapp-evolution-api/whatsapp_evolution_base/models/evolution_api.py`
- `oca/social/mail_gateway_whatsapp/models/mail_gateway_whatsapp.py`

## Evolution API external references (docs incompletas)

- https://docs.evoapicloud.com/api-reference/authentication
- https://www.postman.com/agenciadgcode/evolution-api/collection/nm0wqgt/evolution-api-v2-3
- https://doc.evolution-api.com/v2/api-reference/get-information

## Evolution API (local)

- A Evolution API roda no mesmo servidor via Docker.
- Mantenha o webhook apontando para a URL do gateway no Odoo (sem `?db=`).

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

- Logs nao sao obrigatorios em producao. O addon `mail_discuss_hub_gateway_devtools` adiciona logging quando instalado.
- Nao mover log para o OCA `mail_gateway`; manter extensoes locais (via devtools).

### `mail_discuss_hub_gateway_devtools`

- Guarda o modelo `mail.gateway.webhook.log`, campos em `mail.message`, views e wizards de replay/cleanup.
- Opcional: quando instalado, gateways passam a registrar logs; quando ausente, webhooks processam sem persistir.

### `mail_gateway_whatsapp_common`

- Define DTO `NormalizedPayload` e servico `_process_normalized` (message/reaction/status/delete) com idempotencia.
- Adiciona campos em `mail.message` para id externo, chat, status, quote, reactions e payload bruto.
- Providers apenas convertem o webhook bruto para DTO e chamam o servico.

### `mail_gateway_whatsapp_evolution_api`

- Usa `mail_gateway_whatsapp_common` para criar/atualizar mensagens; foca apenas em parse Evolution → DTO.
- Webhook sem `?db=`; db fixo no `odoo.conf`.
- Divergencias doc/servidor devem ser confrontadas e registradas em `EVOLUTION_API_REFERENCE.md`.

### `mail_gateway_whatsapp_evolution_api`

- Webhook precisa de **db fixo** no `odoo.conf` (Evolution API nao preserva querystring).
- Nao usar `?db=` em webhooks.
- Deduplicacao: use o id externo (Evolution) em `mail.notification.gateway_message_id`.

### `mail_gateway_whatsapp_evolution_api_manager`

- Gerencia servidores/instancias e aplica settings via endpoint da Evolution.
- Nao deve alterar diretamente a logica de gateway (isso fica no addon do gateway).

## Referencias

- Lista de addons: `README.MD`
- Guia Evolution API (endpoints, metodos e payloads): `EVOLUTION_API_REFERENCE.md`
