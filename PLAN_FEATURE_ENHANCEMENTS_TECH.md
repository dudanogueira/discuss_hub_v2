# Planner Tecnico de Melhorias (Discuss Hub)

Proposito
- Guia tecnico e amigavel para IA para evoluir o discuss-hub com ideias de addons de referencia.
- Manter compatibilidade com OCA mail_gateway e Odoo 18.

Baseline atual (discuss-hub)
- mail_discuss_hub: times + settings.
- mail_discuss_hub_gateway: utilitarios de gateway (sidebar), log de webhook, UX de guest.
- mail_gateway_whatsapp_evolution_api: Evolution gateway (webhook, send text/media, dedupe basico).
- mail_gateway_whatsapp_evolution_api_manager: manager de instancia, sync de settings, webhook.

Referencia (ideias principais)

odoo-whatsapp-evolution-api
- whatsapp_evolution_base
  - Instancia com settings completos, eventos webhook, log de mensagens.
  - Controller de webhook com tipos de mensagem, status, reaction, quote.
  - Widget de media preview + download.
  - Verificacao de numero (whatsappNumbers).
- whatsapp_evolution_discuss
  - channel_type=whatsapp com partner+instance.
  - Start conversation via busca de parceiro no Discuss.
  - Reaction send/receive, quoted replies, message id mapping.
  - Botao no chatter para enviar WhatsApp.
- whatsapp_contact_management
  - Contatos privados, promocao, owner, flags de verificacao.
- whatsapp_evolution_ui_utils
  - Widgets de selection com icone.

wa_conn (core)
- Multi contas, webhook, QR connect.
- Template engine com loops/expressoes e variaveis.
- Mass send e acoes automatizadas.
- Design provider-agnostic (normalize inbound).

wa_conn_apps
- Pipeline: stages/tags + kanban.
- Team model e atribuicao.
- Contadores de nao lidas em canal sem membro.
- Send queue (agendado, retry, cron).
- Client action para abrir Discuss com channel.
- Bot framework (flows, comandos, sessoes).
- Providers: Evolution, Quepasa.

Comparacao vs discuss-hub (macro)

- Instance management
  - Referencia: status rico, QR, settings sync.
  - Discuss-hub: sim (manager), mas sem log de mensagens por instancia.
- Message log com status + preview
  - Referencia: whatsapp.message com status e previews.
  - Discuss-hub: so log de webhook (generico).
- Reactions, quotes, edits/deletes
  - Referencia: send/receive reactions, quoted replies, updates.
  - Discuss-hub: ausente.
- Contact verification + private contacts
  - Referencia: flags de verificacao, private/promo.
  - Discuss-hub: ausente.
- Start conversation por partner search
  - Referencia: patch no channel selector.
  - Discuss-hub: ausente.
- Templates + mass send + queue
  - Referencia: template engine, mass send, cron.
  - Discuss-hub: ausente.
- Pipeline stages/tags + teams
  - Referencia: stages/tags e kanban.
  - Discuss-hub: times existem, sem pipeline.
- Bot flows
  - Referencia: flows + sessions.
  - Discuss-hub: ausente.

Consideracoes comparativas (estrategia)
- Discuss-hub eh enxuto e alinhado ao OCA mail_gateway; nao eh "defasado", so menor escopo.
- Addons de referencia sao feature-rich, mas mais invasivos:
  - Criam channel_type proprio e bypass de gateway.
  - Mantem log de mensagem separado (whatsapp.message) e webhooks proprios.
- Copiar a arquitetura inteira aumenta risco e friccao de upgrade.
- Preferir adocao modular mantendo mail_gateway como camada de transporte.
- Usar gateway_id.gateway_type como subtipo; evitar mudar channel_type.
- Equilibrar completeness vs manutencao; manter core estavel e features opt-in.
- Ideias para cherry-pick:
  - reactions, quotes, status updates
  - templates + send queue
  - verificacao e privacidade de contato
  - stages/tags + bot flows

Guardrails
- Manter channel_type = gateway. Usar gateway_id.gateway_type para provider.
- Nao alterar OCA/OCB diretamente.
- Webhook com db fixo (sem ?db=).
- JS patches pequenos e isolados.

Arquitetura alvo (enhanced)
- mail_gateway como camada de transporte.
- Camada business: inbox + atribuicao + status no discuss.channel.
- Metadados no mail.message (remote id, reaction, status).
- Separar em modulos: inbox, contact, templates/queue, bot, analytics.

Modulos propostos (responsabilidades)
- mail_discuss_hub_inbox
  - discuss.channel: discuss_team_id, assigned_user_id, assignment_state.
  - domain helpers + record rules por time.
  - acoes server-side de atribuicao.
- mail_gateway_whatsapp_evolution_api_enhanced
  - message id mapping, reactions, quoted replies, update/delete.
  - parse de status do webhook para mail.message.
- mail_discuss_hub_contact
  - verificacao whatsapp, contato privado, ownership.
- mail_discuss_hub_templates
  - template engine + send queue + mass send.
- mail_discuss_hub_bot
  - bot flows, comandos, sessoes.
- mail_discuss_hub_ui_utils
  - widgets e helpers UI.
- mail_discuss_hub_analytics
  - tempos de resposta, SLA, auditoria de atribuicao.

Roadmap (fases)

Fase 1 - Confiabilidade de mensagens
- Campos em mail.message:
  - gateway_message_id (remote), status, quoted_message_id, flags reaction.
- Eventos webhook:
  - messages.update (read/delivered), messages.delete, reaction.
- Idempotencia por gateway_message_id.
- Mapear webhook log -> message.
- Modulo: mail_gateway_whatsapp_evolution_api_enhanced.

Fase 2 - Inbox model + acesso
- discuss.channel: discuss_team_id, assigned_user_id, assignment_state.
- Record rules: time le canais sem membership.
- Acoes: assign to me/user, unassign, close/reopen.
- Modulo: mail_discuss_hub_inbox.

Fase 3 - Inbox UI (Discuss)
- Sidebar filtros: Minhas, Todas, Nao atribuida, Time.
- Contadores via read_group; ordenacao por last_message_date.
- Acoes inline.
- Modulo: mail_discuss_hub_inbox_ui.

Fase 4 - Contact management
- Verificacao (whatsappNumbers).
- Privado + promocao + owner.
- Sync opcional de avatar.
- Modulo: mail_discuss_hub_contact.

Fase 5 - Templates + Mass Send
- Template engine (safe eval, loops).
- Mass send + queue + cron.
- Rate limit + retry.
- Modulo: mail_discuss_hub_templates.

Fase 6 - Bot e automacoes
- Bot flow (message/question/condition/action/wait).
- Command handlers + sessions.
- Triggers via webhook.
- Modulo: mail_discuss_hub_bot.

Fase 7 - UX polish
- Media preview no mail.message.
- Start conversation via partner search.
- Botoes de lead/cotacao no Discuss.
- Modulo: mail_discuss_hub_ui_utils + mail_discuss_hub_inbox_ui.

Fase 8 - Analytics
- SLA (first response, resolution).
- Auditoria de atribuicao.
- Dashboards.
- Modulo: mail_discuss_hub_analytics.

Guia de execucao (por feature)
1) Data model
   - Campos claros + indices.
   - Constraints quando necessario.
2) Security
   - Record rules por empresa/time.
3) Webhook
   - Mapear eventos para status/reaction/quote.
   - Idempotencia por remote id.
4) UI
   - Views minimas.
   - Patch Discuss so quando preciso.
5) Tests
   - Unit tests de parsing e dedupe.
   - Mock de payloads Evolution.

Extracts para considerar
- Reaction handling (send + receive).
- Quoted replies via stanzaId.
- Media download + preview.
- Partner search para abrir conversa.
- Verificacao e privacidade de contato.
- Pipeline stages/tags.
- Send queue com retry.
- Bot flow engine.

Riscos
- Mudar channel_type quebra gateway; evitar.
- Patches JS sensiveis a upgrades; manter pequenos.
- Record rules podem expor dados; sempre filtrar por company/time.

---

## Analise Comparativa Profunda (Claude Opus 4.5 - 2026-01-15)

Esta secao documenta uma analise detalhada do `discuss_hub_legacy` confrontando
com o discuss-hub atual e validando as premissas deste planner.

### Estrutura do discuss_hub_legacy

O modulo legado eh um **monolito completo** com as seguintes partes:

1. **discuss_hub.connector** (~350 linhas)
   - Multi-provider: Evolution, NotificaMe, WhatsApp Cloud
   - Factory pattern: `get_plugin()` via `importlib`
   - Settings inline: templates Jinja2, read receipts, reactions, profile picture
   - QR code display na view
   - Routing inicial: `automatic_added_partners`, `automatic_added_teams`

2. **Plugin Evolution** (~1263 linhas)
   - Handlers para TODOS os tipos: text, image, video, audio, location, document, contact
   - **Reactions**: `handle_reaction_message()` cria `mail.message.reaction`
   - **Quoted replies**: via stanzaId → busca `discuss_hub_message_id` → `parent_id`
   - **Read status**: `messages.update` → `_mark_as_read()` no channel member
   - **Delete**: `messages.delete` → strikethrough + mensagem de alerta
   - **Contacts sync**: `contacts.upsert` com profile picture
   - Campo critico: `discuss_hub_message_id` no `mail.message`

3. **discuss.channel estendido**
   - `discuss_hub_connector` (Many2one para connector)
   - `discuss_hub_outgoing_destination` (numero destino)
   - Override `message_post()` → outgoing direto
   - Override `_notify_thread()` → bot automation
   - Actions: join, leave, forward wizard, archive wizard

4. **discuss_hub.routing_team** (~200 linhas)
   - Estrategias: round_robin, random, least_busy
   - `online_users_only` filter
   - Team members com contador para round robin
   - Wizard de forward com nota

5. **discuss_hub.bot_manager** (~553 linhas)
   - Tipos: generic HTTP, Typebot
   - Session management
   - Responde a external/portal/public users
   - Configuravel para DMs de internal users
   - Audio extraction para bots de voz

### Matriz de Features: Legacy vs Atual

| Feature | Legacy | Discuss-hub Atual | Gap |
|---------|--------|-------------------|-----|
| `gateway_message_id` em mail.message | ✅ `discuss_hub_message_id` | ❌ So em `mail.notification` | CRITICO |
| Reactions receive | ✅ `handle_reaction_message()` | ❌ | ALTO |
| Reactions send | ✅ `outgo_reaction()` | ❌ | ALTO |
| Quoted replies | ✅ stanzaId → parent_id | ❌ | ALTO |
| Read status (delivered/read) | ✅ `_mark_as_read()` | ❌ | MEDIO |
| Message delete | ✅ strikethrough + alerta | ❌ | MEDIO |
| Routing teams | ✅ round_robin/random/least_busy | ⚠️ So `mail.discuss.team` sem routing | MEDIO |
| Bot framework | ✅ Typebot + generic HTTP | ❌ | ALTO |
| Inbox assignment | ❌ | ❌ | (nenhum tem) |
| Record rules por time | ❌ | ❌ | (nenhum tem) |
| Alinhamento OCA mail_gateway | ❌ Bypass completo | ✅ Herda `mail.gateway.abstract` | VANTAGEM ATUAL |
| Separacao de modulos | ❌ Monolito | ✅ Modular | VANTAGEM ATUAL |
| Multi-gateway futuro | ❌ Acoplado a Evolution | ✅ Abstrato | VANTAGEM ATUAL |

### Problemas Arquiteturais do Legacy

1. **Bypass do OCA mail_gateway**
   - Controller proprio: `/discuss_hub/connector/<uuid>`
   - Nao usa `mail.gateway.abstract`
   - Incompativel com outros gateways OCA (Telegram, etc.)

2. **Acoplamento forte Provider ↔ Channel**
   - `discuss.channel.discuss_hub_connector` diretamente
   - Nao usa `gateway_channel_token`, `gateway_id`
   - Vai contra a abstracao de gateway

3. **Plugin monolitico**
   - `plugins/evolution.py` com 1263 linhas
   - Mistura: parsing webhook + API client + message handling
   - Dificil de testar isoladamente

4. **Antipatterns**
   - `self.env.cr.commit()` manual (comentado mas presente)
   - Templates Jinja2 inline sem sandbox
   - Factory pattern via `importlib` (fragil)

### Vantagens Arquiteturais do Atual

1. **Heranca correta de `mail.gateway.abstract`**
   - `_receive_update()`, `_send()`, `_set_webhook()`, `_remove_webhook()`
   - Compativel com qualquer gateway OCA

2. **Separacao clara em arquivos**
   - `evolution_api_client.py` → HTTP client isolado
   - `evolution_settings_mixin.py` → settings reutilizaveis
   - `evolution_webhook_event.py` → eventos configuráveis
   - `mail_gateway_whatsapp_evolution_api.py` → handler principal

3. **Dedupe via `mail.notification.gateway_message_id`**
   - Consistente com design OCA
   - Porem insuficiente para quotes/reactions

4. **Modulos por responsabilidade**
   - `mail_discuss_hub` → times
   - `mail_discuss_hub_gateway` → logs webhook
   - `mail_gateway_whatsapp_evolution_api` → gateway
   - `mail_gateway_whatsapp_evolution_api_manager` → instancias

### Recomendacoes de Cherry-Pick

**Copiar logica de negocio do legacy, NAO a arquitetura:**

1. **CRITICO: Adicionar `gateway_message_id` em mail.message**
   ```python
   # Em mail_gateway_whatsapp_evolution_api_enhanced
   class MailMessage(models.Model):
       _inherit = "mail.message"
       gateway_message_id = fields.Char(index=True)
   ```
   Isso desbloqueia: reactions, quotes, status updates, deletes.

2. **Copiar handlers de mensagem do legacy**
   - `handle_reaction_message()` → adaptar para usar `gateway_message_id`
   - `handle_text_message()` com logica de stanzaId → parent_id
   - `process_messages_update()` → read status
   - `process_messages_delete()` → strikethrough

3. **Copiar routing strategies**
   - `round_robin`, `random`, `least_busy`
   - Adaptar para `mail.discuss.team`

4. **NAO copiar**
   - Controller proprio (usar OCA)
   - Campos em `discuss.channel` (usar `gateway_channel_token`)
   - Plugin factory pattern (manter arquivos separados)
   - Jinja2 inline (usar template engine seguro)

### Ajustes no Roadmap

**Fase 1 deve ser expandida:**

Antes:
- Campos em mail.message: gateway_message_id, status, quoted_message_id

Depois (expandido):
- Campos em mail.message:
  - `gateway_message_id` (Char, indexed) ← ID remoto da Evolution
  - `gateway_message_status` (Selection: pending/sent/delivered/read/failed)
  - `gateway_quoted_message_id` (Many2one → mail.message)
- Eventos webhook a processar:
  - `messages.upsert` → ja existe, adicionar stanzaId parsing
  - `messages.update` → read/delivered status
  - `messages.delete` → strikethrough + alerta opcional
  - Reactions em `messages.upsert` com `reactionMessage`
- Idempotencia:
  - Buscar por `gateway_message_id` antes de criar
  - Suportar re-delivery de webhook
- Reaction handling:
  - Receber: criar `mail.message.reaction`
  - Enviar: `outgo_reaction()` via Evolution API

**Nova Fase 1.5 - Bot Framework (se priorizado):**
- Modelo `mail.discuss.bot`
- Tipos: generic HTTP, Typebot
- Trigger via `_notify_thread()` override
- Session management por channel

### Codigo de Referencia para Cherry-Pick

**Localizacao no legacy:**
- Reactions: `plugins/evolution.py:handle_reaction_message()` (linhas ~800-850)
- Quoted replies: `plugins/evolution.py:handle_text_message()` (linhas ~750-800)
- Read status: `plugins/evolution.py:process_messages_update()` (linhas ~1100-1180)
- Delete: `plugins/evolution.py:process_messages_delete()` (linhas ~1200-1260)
- Routing: `routing_manager.py:_get_round_robin_user()` (linhas ~80-100)
- Bot: `bot_manager.py` (arquivo inteiro)

**Payloads Evolution API (do legacy):**
```python
# Reaction receive
data.get("message", {}).get("reactionMessage", {})
# -> key.id = original message id
# -> text = emoji

# Quoted reply
data.get("contextInfo", {}).get("stanzaId")  # ID da mensagem citada
data.get("contextInfo", {}).get("quotedMessage")  # conteudo

# Read status
payload.get("data", {}).get("status") == "READ"
payload.get("data", {}).get("keyId")  # message id

# Delete
payload.get("data", {}).get("id")  # message id deletado
```

### Conclusao (discuss_hub_legacy)

O `discuss_hub_legacy` eh **muito mais feature-complete** do que a documentacao
anterior sugeria. Porem, sua arquitetura eh **incompativel com OCA** e criaria
divida tecnica significativa.

A estrategia correta eh:
1. Manter arquitetura OCA do discuss-hub atual
2. Cherry-pick agressivo de logica de negocio do legacy
3. Priorizar Fase 1 expandida (message reliability)
4. Considerar bot framework como Fase 1.5 se for prioridade de negocio

O discuss-hub atual esta **atras em features, mas a frente em fundacao**.
O trabalho eh fechar o gap de features sem comprometer a arquitetura.

---

## Analise Comparativa: wa_conn (Claude Opus 4.5 - 2026-01-15)

Esta secao documenta uma analise detalhada do ecossistema `wa_conn` 
(repositorios `wa_conn` standalone e `wa_conn_apps`) confrontando com 
o discuss-hub atual.

### Estrutura do Ecossistema wa_conn

O wa_conn eh dividido em dois repositorios com filosofias complementares:

#### 1. wa_conn (standalone) - Base Simples

Modulo base com foco em **envio de mensagens via automacoes Odoo**:

**Modelos principais:**
- `wa.account` (~280 linhas): conta WhatsApp com conexao Evolution API
- `wa.template` (~180 linhas): templates com render Jinja2-like
- `wa.compose` (~120 linhas): wizard para envio manual
- `wa.mass.send` (~200 linhas): envio em massa com delay aleatorio
- `wa.mixin` (~90 linhas): mixin abstrato para envio
- `wa.message` (~20 linhas): modelo simples de mensagem

**Integracao com ir.actions.server:**
- Novo tipo de acao: `send_whatsapp_message`
- Permite usar WhatsApp em Automated Actions nativas do Odoo
- Suporta templates dinamicos com variaveis do record

**Controller basico:**
- `/webhook` para receber eventos
- Handlers para messages.upsert/update/delete (parciais)

**Template Engine:**
- Suporta `{{ field_name }}` e `{{ object.field_name }}`
- For loops: `{% for line in lines %}...{% endfor %}`
- Funcao `format_currency(amount, currency_id)`
- Usa eval() sem sandbox (RISCO)

#### 2. wa_conn_apps - Ecossistema Completo

Conjunto de modulos com arquitetura **provider-agnostic**:

**wa_conn (core expandido):**
- `wa.account` base slim com interface abstrata
- `wa.channel` estende `discuss.channel` com `channel_type=whatsapp`
- `wa.team` para times de atendimento
- `wa.channel.stage` e `wa.channel.tag` para pipeline kanban
- `wa.send.queue` para fila de envio com retry
- `NormalizedPayload` DTO para normalizar webhooks

**wa_conn_evolution:**
- Provider Evolution API
- Implementa `normalize_inbound()`, `send_text()`, `send_media()`
- Adiciona campos especificos via heranca

**wa_conn_bot:**
- `wa.bot`: configuracao de bot com greeting, timeout, modos de init
- `wa.bot.flow`: steps de fluxo (message, question, condition, action, wait)
- `wa.bot.command`: comandos customizados com codigo Python
- `wa.bot.session`: sessoes com variaveis, timeout, estado

### Arquitetura wa_conn_apps (diagrama)

```
wa.account (base abstrato)
    |
    +-- wa_conn_evolution (provider)
    |       normalize_inbound(), send_text(), send_media()
    |
    +-- wa_conn_quepasa (provider)
            normalize_inbound(), send_text(), send_media()

discuss.channel
    |
    +-- wa.channel (extend)
            is_wa, wa_partner_id, wa_account_id
            stage_id, tag_ids, note
            wa_unread_count, wa_unread_member_count

wa.bot
    |
    +-- wa.bot.flow (steps)
    +-- wa.bot.command (comandos)
    +-- wa.bot.session (sessoes)
```

### Pontos Fortes do wa_conn_apps

1. **Provider-Agnostic Design**
   - Interface abstrata em `wa.account`
   - Metodos `normalize_inbound()`, `send_text()`, `send_media()`, `send_reaction()`, `send_reply()`
   - Adicionar novo provider = criar novo modulo com heranca

2. **DTO para Normalizacao**
   ```python
   class NormalizedPayload:
       provider, instance, event
       message_id, remote_jid, mobile
       from_me, push_name, message, message_type
       mime_type, attachment_b64, attachment_name
   ```
   - Payload normalizado independente de provider
   - Facilita testes e debug

3. **Pipeline Kanban**
   - `wa.channel.stage` com group_expand para kanban
   - `wa.channel.tag` para labels
   - `sequence` para ordenacao manual
   - `note` para anotacoes

4. **Send Queue Robusto**
   - `wa.send.queue` com status (pending/sending/sent/error/cancelled)
   - Retry com attempts counter
   - Cron `cron_process_send_queue` em lotes
   - Delay aleatorio entre mensagens

5. **Bot Framework Completo**
   - Modos de init: auto, command, timeout
   - Flow steps: message, question, condition, action, wait
   - Validacao de respostas: none, text, number, email, phone, custom
   - Sessoes com variaveis JSON e timeout configuravel
   - Expressoes Python para condicoes

6. **Contadores de Nao-Lidas**
   - `wa_unread_count`: mensagens quando nenhum user joined
   - `wa_unread_member_count`: para o membro atual
   - Broadcast via bus quando mensagem chega sem membros

### Problemas do wa_conn_apps

1. **channel_type proprio**
   - `channel_type='whatsapp'` em vez de usar gateway
   - Incompativel com OCA mail_gateway
   - Cria silos de codigo

2. **Dependencia de base_automation**
   - Manifesto depende de `base_automation`
   - Logica de envio via ir.actions.server
   - Nao usa o fluxo padrao de mail.gateway

3. **eval() sem sandbox**
   - Template engine usa eval() direto
   - Bot flow usa eval() para condicoes
   - Risco de injecao de codigo

4. **Nao processa reactions/quotes no inbound**
   - `normalize_inbound()` nao extrai reactions
   - Falta mapeamento de stanzaId para replies
   - Interface existe (`inbound_handle_reaction`, `inbound_handle_reply`) mas nao implementada

5. **Sem integracao com mail.message**
   - Usa `message_type='whatsapp'` customizado
   - Nao popula `gateway_message_id` no mail.message
   - Perde rastreabilidade

### Matriz Comparativa Completa

| Feature | wa_conn_apps | discuss_hub_legacy | discuss-hub atual |
|---------|-------------|-------------------|-------------------|
| Provider-agnostic | ✅ Interface abstrata | ❌ Plugin factory | ⚠️ Heranca gateway |
| Alinhamento OCA | ❌ channel_type proprio | ❌ Bypass completo | ✅ mail.gateway |
| DTO normalizado | ✅ NormalizedPayload | ❌ Inline parsing | ❌ Inline parsing |
| Pipeline stages | ✅ wa.channel.stage | ❌ | ❌ |
| Tags | ✅ wa.channel.tag | ❌ | ❌ |
| Send queue | ✅ wa.send.queue | ❌ | ❌ |
| Mass send | ✅ Cron + delay | ✅ Basic | ❌ |
| Bot framework | ✅ Completo | ✅ Typebot + generic | ❌ |
| Bot flow builder | ✅ wa.bot.flow | ❌ Apenas code | ❌ |
| Bot sessions | ✅ wa.bot.session | ✅ | ❌ |
| Reactions receive | ⚠️ Interface, nao impl | ✅ Completo | ❌ |
| Reactions send | ✅ send_reaction() | ✅ outgo_reaction() | ❌ |
| Quoted replies | ⚠️ Interface, nao impl | ✅ stanzaId | ❌ |
| Read status | ❌ | ✅ _mark_as_read() | ❌ |
| Message delete | ⚠️ Handler vazio | ✅ strikethrough | ❌ |
| Unread counters | ✅ wa_unread_count | ❌ | ❌ |
| Template engine | ✅ Jinja-like + loops | ✅ Jinja2 | ❌ |
| Teams | ✅ wa.team | ✅ routing_team | ✅ mail.discuss.team |
| Routing strategies | ❌ | ✅ round_robin/random | ❌ |
| ir.actions.server | ✅ send_whatsapp_message | ❌ | ❌ |

### Ideias para Cherry-Pick do wa_conn_apps

**Alta prioridade (arquitetura):**
1. **NormalizedPayload DTO** - Criar classe similar para normalizar webhooks
2. **Send Queue** - `mail.gateway.send.queue` com status e retry
3. **Pipeline Stages** - `mail.discuss.channel.stage` (se inbox for prioridade)

**Media prioridade (features):**
4. **Bot Flow Builder** - Adaptar wa.bot.flow para mail.discuss.bot.flow
5. **Tags** - `mail.discuss.channel.tag` para labels
6. **Template Engine** - Versao com sandbox (safe_eval)

**Baixa prioridade (UX):**
7. **Unread Counters** - Logica de wa_unread_count
8. **ir.actions.server integration** - Tipo de acao WhatsApp

### Codigo de Referencia wa_conn_apps

**Localizacoes:**
- DTO: `wa_conn/models/dto.py` (arquivo completo)
- Send Queue: `wa_conn/models/wa_send_queue.py` (linhas 1-100)
- Pipeline: `wa_conn/models/wa_channel_stage.py`, `wa_channel_tag.py`
- Bot Flow: `wa_conn_bot/models/wa_bot_flow.py` (linhas 1-200)
- Bot Session: `wa_conn_bot/models/wa_bot_session.py` (linhas 1-100)
- Unread Count: `wa_conn/models/wa_channel.py` (linhas 40-80)

**Interfaces abstratas (wa.account):**
```python
def normalize_inbound(self, raw, request=None):
    """Normaliza webhook para NormalizedPayload"""

def send_text(self, mobile, message):
    """Envia texto"""

def send_media(self, mobile, *, caption='', b64=None, mime=None, filename=None):
    """Envia media"""

def send_reaction(self, key, reaction):
    """Envia reacao - key: {remoteJid, id, fromMe}"""

def send_reply(self, mobile, message, reply_to=None):
    """Envia reply com threading"""
```

**Pipeline Kanban (wa.channel):**
```python
stage_id = fields.Many2one('wa.channel.stage', group_expand='_read_group_stage_ids')
tag_ids = fields.Many2many('wa.channel.tag')
sequence = fields.Integer(index=True)

@api.model
def _read_group_stage_ids(self, stages, domain, order=None):
    return self.env['wa.channel.stage'].search([], order=order or 'sequence,id')
```

### Conclusao Comparativa Final

**Ranking por area:**

| Area | 1º Lugar | 2º Lugar | 3º Lugar |
|------|----------|----------|----------|
| Arquitetura OCA | discuss-hub | wa_conn_apps | legacy |
| Features prontas | legacy | wa_conn_apps | discuss-hub |
| Bot framework | wa_conn_apps | legacy | discuss-hub |
| Pipeline/UX | wa_conn_apps | - | - |
| Message reliability | legacy | discuss-hub | wa_conn_apps |
| Extensibilidade | wa_conn_apps | discuss-hub | legacy |

**Recomendacao estrategica atualizada:**

1. **Manter base OCA** do discuss-hub atual (vantagem arquitetural)

2. **Cherry-pick de logica do legacy:**
   - Reactions, quotes, read status, delete
   - Campo `gateway_message_id` no mail.message

3. **Cherry-pick de arquitetura do wa_conn_apps:**
   - DTO `NormalizedPayload` para webhooks
   - Send Queue com retry
   - Bot flow builder (se prioridade)

4. **Evitar:**
   - channel_type customizado (ambos)
   - Template engine com eval() (ambos)
   - Plugin factory via importlib (legacy)

**Proximos passos sugeridos (ordem):**
1. Fase 1: Message reliability (campos + eventos) - base do legacy
2. Fase 1.5: DTO normalizado - arquitetura do wa_conn_apps
3. Fase 2: Inbox model - novo
4. Fase 3: Send Queue - base do wa_conn_apps
5. Fase 4: Bot framework - merge de ambos

---

## Consideracoes Arquiteturais: mail_gateway vs NormalizedPayload (Claude Opus 4.5)

### Como o OCA mail_gateway funciona

O `mail_gateway` fornece **infraestrutura de roteamento**, nao normalizacao:

```python
# Controller (mail_gateway/controllers/gateway.py)
@route("/gateway/<string:usage>/<string:token>/update", ...)
def post_update(self, usage, token, **kwargs):
    # 1. Recebe JSON cru
    jsonrequest = json.loads(request.httprequest.get_data())
    
    # 2. Resolve o dispatcher pelo gateway_type
    dispatcher = request.env[f"mail.gateway.{usage}"]  # ex: mail.gateway.whatsapp_evolution_api
    
    # 3. Valida
    dispatcher._verify_update(bot_data, jsonrequest)
    
    # 4. Passa payload RAW para o provider
    dispatcher._receive_update(gateway, jsonrequest)  # ← payload cru!
```

### O que cada camada faz

| Camada | Responsabilidade |
|--------|------------------|
| `mail_gateway` (OCA) | URL do webhook, roteamento, seguranca, verificacao |
| `mail.gateway.{type}` | Parsing do payload especifico do provider |
| `_receive_update()` | Recebe payload raw, extrai dados, cria records |

### Por que o OCA nao normaliza?

**Cada provider tem formato completamente diferente:**

```python
# Evolution API
{
  "event": "messages.upsert",
  "data": {
    "key": {"remoteJid": "5511999999999@s.whatsapp.net", "id": "ABC123"},
    "message": {"conversation": "Olá!"},
    "pushName": "João"
  }
}

# Telegram
{
  "update_id": 123456,
  "message": {
    "message_id": 789,
    "from": {"id": 111, "first_name": "João"},
    "text": "Olá!"
  }
}

# WhatsApp Cloud (Meta)
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "5511999999999",
          "text": {"body": "Olá!"}
        }]
      }
    }]
  }]
}
```

O OCA eh **gateway-agnostic** - suporta Telegram, WhatsApp, qualquer coisa.
Nao faz sentido normalizar no core porque cada provider eh diferente.

### Onde o NormalizedPayload faz sentido?

**Dentro do nosso provider** (`mail_gateway_whatsapp_evolution_api`):

```
mail_gateway_whatsapp_evolution_api/
├── models/
│   ├── normalized_payload.py      # ← DTO interno ao provider
│   └── mail_gateway_whatsapp_evolution_api.py
│
│   def _receive_update(self, gateway, update):
│       # 1. Normaliza payload cru para DTO
│       dto = NormalizedPayload.from_evolution(update)
│       
│       # 2. Usa DTO para logica de negocio
│       if dto.event == 'messages.upsert':
│           self._process_message(gateway, dto)
│       elif dto.event == 'messages.update':
│           self._process_status(gateway, dto)
```

### Beneficios do DTO interno

1. **Separacao de concerns**: parsing isolado da logica de negocio
2. **Testabilidade**: mock do DTO, nao do payload raw
3. **Legibilidade**: `dto.message` em vez de `update.get('data',{}).get('message',{}).get('conversation')`
4. **Reutilizacao**: se tivermos Evolution + Quepasa (formatos similares), compartilham DTO

### Quando NAO usar DTO?

- Se o provider for simples (poucos eventos)
- Se o parsing for trivial
- Se nao houver necessidade de testes unitarios do parsing

### Decisao para discuss-hub

**Recomendacao:** Implementar DTO interno no `mail_gateway_whatsapp_evolution_api`:

```python
# models/normalized_payload.py
class NormalizedPayload:
    """DTO para normalizar webhooks Evolution API."""
    
    def __init__(self, **kw):
        self.event = kw.get('event')              # messages.upsert, messages.update, etc.
        self.message_id = kw.get('message_id')    # ID remoto da mensagem
        self.remote_jid = kw.get('remote_jid')    # 5511999999999@s.whatsapp.net
        self.mobile = kw.get('mobile')            # 5511999999999
        self.from_me = kw.get('from_me', False)   # enviada por nos?
        self.push_name = kw.get('push_name')      # nome do contato
        self.message = kw.get('message', '')      # texto da mensagem
        self.message_type = kw.get('message_type')  # text, image, audio, etc.
        self.quoted_message_id = kw.get('quoted_message_id')  # stanzaId se reply
        self.reaction_emoji = kw.get('reaction_emoji')  # emoji se reaction
        self.status = kw.get('status')            # READ, DELIVERED, etc.
        self.attachment_b64 = kw.get('attachment_b64')
        self.attachment_name = kw.get('attachment_name')
        self.mime_type = kw.get('mime_type')
        self.raw = kw.get('raw', {})              # payload original
    
    @classmethod
    def from_evolution(cls, raw):
        """Factory para criar DTO a partir de payload Evolution."""
        data = raw.get('data', {})
        key = data.get('key', {})
        message = data.get('message', {})
        context_info = message.get('extendedTextMessage', {}).get('contextInfo', {})
        
        return cls(
            event=raw.get('event'),
            message_id=key.get('id'),
            remote_jid=key.get('remoteJid'),
            mobile=key.get('remoteJid', '').split('@')[0],
            from_me=key.get('fromMe', False),
            push_name=data.get('pushName'),
            message=message.get('conversation') or message.get('extendedTextMessage', {}).get('text', ''),
            message_type=data.get('messageType'),
            quoted_message_id=context_info.get('stanzaId'),
            reaction_emoji=message.get('reactionMessage', {}).get('text'),
            status=data.get('status'),
            attachment_b64=message.get('base64'),
            raw=raw,
        )
```

**Isso nao conflita com OCA** - eh apenas organizacao interna do nosso provider.

---

## Observacao: Legacy NAO tem DTO (Claude Opus 4.5)

### Como o legacy faz parsing

O `discuss_hub_legacy` **nao implementa normalizacao**. O parsing eh feito inline com `.get()` em cascata:

```python
# discuss_hub_legacy/models/plugins/evolution.py
def process_messages_upsert(self, payload):
    data = payload.get("data", {})
    remote_jid = data.get("key", {}).get("remoteJid")  # ← inline
    message_id = self.get_message_id(payload)
    # ...
    
    message = data.get("message", {})
    if message.get("conversation"):
        response = self.handle_text_message(payload, channel, partner)
    elif message.get("reactionMessage"):
        response = self.handle_reaction_message(data, channel, partner, message_id)
    # ... cada handler repete extracao
```

### Problemas do approach inline

1. **Repeticao** - Cada handler (`handle_text_message`, `handle_image_message`, etc.) reextrai dados do payload
2. **Acoplamento alto** - Formato Evolution hardcoded em toda a codebase
3. **Dificil testar** - Precisa mock de payload completo para cada teste
4. **Ilegivel** - `payload.get('data',{}).get('key',{}).get('remoteJid')` vs `dto.remote_jid`

### Comparacao direta

| Aspecto | Legacy | wa_conn_apps | discuss-hub (proposta) |
|---------|--------|--------------|------------------------|
| Normalizacao | ❌ Inline `.get()` | ✅ `NormalizedPayload` DTO | ✅ DTO interno |
| Parsing centralizado | ❌ Espalhado | ✅ Factory method | ✅ Factory method |
| Testabilidade | ❌ Dificil | ✅ Mock DTO | ✅ Mock DTO |
| Legibilidade | ❌ Verboso | ✅ Atributos | ✅ Atributos |

### Conclusao

O DTO que propomos **nao eh cherry-pick do legacy** - eh uma **melhoria arquitetural** inspirada no wa_conn_apps.

**O que o legacy oferece para cherry-pick:**
- Logica de negocio (reactions, quotes, read status, delete)
- Campo `discuss_hub_message_id` no mail.message
- Handlers para tipos de mensagem

**O que wa_conn_apps oferece para cherry-pick:**
- Padrao DTO para normalizacao
- Send Queue com retry
- Bot flow builder

**Estrategia final:** Combinar logica do legacy com arquitetura do wa_conn_apps.

---

## Analise Comparativa: odoo-whatsapp-evolution-api (Claude Opus 4.5)

### Estrutura do Projeto

| Modulo | Linhas (aprox) | Funcao |
|--------|----------------|--------|
| `whatsapp_evolution_base` | ~1500 | Core: instance, API abstraction, webhook, message log |
| `whatsapp_evolution_discuss` | ~400 | Integracao Discuss: channel type, envio bidirecional |
| `whatsapp_contact_management` | ~400 | Gestao de contatos: privados, verificacao, sanitizacao |
| `whatsapp_evolution_ui_utils` | ~50 | Assets JS/CSS helper |

### Arquitetura - Pontos Positivos

1. **API abstraction layer** - Modelo `whatsapp.evolution.api` isola HTTP requests
2. **Message log model** - `whatsapp.message` com todos os campos (status, quoted, media_url, raw_json)
3. **Campos no mail.message** - `whatsapp_message_id_str` e `whatsapp_status`
4. **Contact sanitization** - Campo computado `mobile_sanitized` para buscas eficientes
5. **Verificacao WhatsApp** - Botao para verificar se numero tem WhatsApp via API
6. **Contatos privados** - Sistema de `is_private` + `owner_user_id` com promocao/reversao
7. **Instance type** - Suporte a instancia de empresa vs usuario individual
8. **Botao WhatsApp no Chatter** - Envio manual de qualquer record

### Arquitetura - Pontos Negativos

1. **channel_type customizado** - Usa `whatsapp` em vez de `group` (mesmo problema do legacy)
2. **Sem DTO/normalizacao** - Parsing inline no webhook controller (~200 linhas)
3. **Sem send queue** - Envio direto sem retry
4. **Sem bot framework** - Nenhuma automacao
5. **Nao usa mail_gateway OCA** - Arquitetura propria

### Feature: Botao WhatsApp no Chatter

```
┌─────────────────────────────────────────────────────────────────┐
│  Pedido de Venda (sale.order)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Chatter:                                                       │
│  [Send message] [Log note] [WhatsApp] [Schedule activity]       │
│                            ↑ BOTAO NOVO                         │
│                                                                 │
│  Clica → Abre Wizard:                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Send From: [Evolution Instance 1]                           ││
│  │ Recipient: [Cliente ABC]  ← pre-preenchido do partner_id    ││
│  │ Message: [____________________________]                     ││
│  │ Attachments: [+ Upload]                                     ││
│  │ [Send] [Cancel]                                             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Componentes:**
- `chatter.xml` - Adiciona botao na topbar
- `chatter_patch.js` - Intercepta clique e abre wizard
- `whatsapp_composer.py` - Wizard transient model
- `whatsapp_composer_views.xml` - Form do wizard

### Comparacao Geral Atualizada

| Aspecto | odoo-whatsapp-evolution-api | discuss_hub_legacy | wa_conn_apps | discuss-hub (OCA) |
|---------|----------------------------|-------------------|--------------|-------------------|
| Arquitetura OCA | ❌ | ❌ | ❌ | ✅ |
| API abstraction | ✅ | ❌ | ✅ | ❌ |
| Message log model | ✅ | ❌ | ❌ | ❌ |
| DTO normalizado | ❌ | ❌ | ✅ | ❌ |
| Send Queue | ❌ | ❌ | ✅ | ❌ |
| Bot framework | ❌ | ✅ | ✅ | ❌ |
| Contact management | ✅ | ❌ | ❌ | ❌ |
| Botao Chatter | ✅ | ❌ | ❌ | ❌ |
| base_automation | ❌ | ✅ | ✅ | ❌ |

### Cherry-pick deste modulo

1. **API abstraction layer** - Modelo para isolar requests
2. **Message log model** - `whatsapp.message` com campos completos
3. **Contact sanitization** - Campo `mobile_sanitized`
4. **Private contacts** - Sistema `is_private` + `owner_user_id`
5. **WhatsApp verification** - Botao para verificar numero
6. **Botao WhatsApp no Chatter** - Wizard de envio manual

---

## Feature: base_automation para Envio Automatico (Claude Opus 4.5)

### O que eh

O `base_automation` do Odoo permite criar acoes automatizadas baseadas em gatilhos.
O wa_conn **estende** o `ir.actions.server` para adicionar um novo tipo de acao: **Send WhatsApp**.

### Como funciona

```python
# ir_actions_server.py (wa_conn)
class WAServerAction(models.Model):
    _inherit = 'ir.actions.server'
    
    # Adiciona novo tipo de acao
    state = fields.Selection(
        selection_add=[('send_wa_message', 'Send WhatsApp')],
    )
    
    # Campos especificos
    wa_account_id = fields.Many2one('wa.account')
    wa_template_id = fields.Many2one('wa.template')
    wa_message = fields.Text()
    model_partner = fields.Boolean()  # Enviar para partner do record
    partner_ids = fields.Many2many('res.partner')  # Destinatarios fixos
```

### Fluxo de uso

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings > Technical > Automation > Automated Actions         │
├─────────────────────────────────────────────────────────────────┤
│  Trigger: [On Creation] [On Update] [Based on Time]            │
│  Model: Sale Order                                             │
│  Filter: [('state', '=', 'sale')]                              │
│                                                                 │
│  Action to do: [Send WhatsApp]  ← NOVO TIPO                    │
│                                                                 │
│  Gateway: [Evolution Instance 1]                               │
│  Template: [Confirmacao de Venda]                              │
│  [x] Model Partner (envia para cliente do pedido)              │
└─────────────────────────────────────────────────────────────────┘
```

### Casos de uso

- "Quando pedido for confirmado, enviar WhatsApp para cliente"
- "Quando fatura vencer em 3 dias, enviar lembrete"
- "Quando lead for criado, enviar mensagem de boas-vindas"
- "Quando ticket for fechado, enviar pesquisa de satisfacao"

### Diferenca do Bot Framework

| Componente | Direcao | Trigger |
|------------|---------|---------|
| `base_automation` | ERP → WhatsApp | Eventos do ERP (venda, fatura, etc) |
| `Bot Framework` | WhatsApp → ERP | Mensagens recebidas (palavra-chave, etc) |

**Sao complementares!**

### Beneficio

Permite criar automacoes **sem codigo**, tudo pela interface do Odoo.

---

## Roadmap Atualizado (Claude Opus 4.5)

### Fase 1: Message Reliability (Base do Legacy)
- [ ] Campo `gateway_message_id` no mail.message
- [ ] Tracking de status (sent, delivered, read)
- [ ] Eventos messages.update

### Fase 1.5: DTO Normalizado (Arquitetura wa_conn_apps)
- [ ] Classe `NormalizedPayload` no provider
- [ ] Factory `from_evolution()` para parsing centralizado
- [ ] Refatorar `_receive_update()` para usar DTO

### Fase 2: Inbox Model (Novo)
- [ ] Modelo `mail.gateway.inbox` para pipeline
- [ ] Kanban com stages customizaveis
- [ ] Atribuicao de atendente

### Fase 3: Send Queue (Base wa_conn_apps)
- [ ] Modelo `mail.gateway.send.queue`
- [ ] Status: pending, sent, failed, retry
- [ ] Cron para processar fila
- [ ] Retry automatico

### Fase 4: Bot Framework (Merge Legacy + wa_conn_apps)
- [ ] Modelo `mail.gateway.bot`
- [ ] Matching por keyword/regex
- [ ] Acoes: resposta, routing, webhook
- [ ] Possivelmente flow builder visual

### Fase 5: Chatter Integration (Base odoo-whatsapp-evolution-api)
- [ ] Botao WhatsApp no Chatter de qualquer record
- [ ] Wizard `gateway.whatsapp.composer`
- [ ] Pre-preenchimento de partner_id
- [ ] Log da mensagem no chatter

### Fase 6: base_automation Integration (Base wa_conn)
- [ ] Herdar `ir.actions.server`
- [ ] Novo tipo: `send_gateway_message`
- [ ] Campos: gateway_id, template_id, message, model_partner
- [ ] View para configurar campos WhatsApp na automation

### Fase 7: Contact Management (Base odoo-whatsapp-evolution-api)
- [ ] Campo `mobile_sanitized` computado
- [ ] Sistema de contatos privados (`is_private`)
- [ ] Verificacao de numero WhatsApp via API
- [ ] Promocao/reversao de contato privado

### Prioridade Sugerida

1. **Alta:** Fase 1, 1.5, 5 (fundacao + UX imediata)
2. **Media:** Fase 2, 3, 6 (pipeline + automacao)
3. **Baixa:** Fase 4, 7 (bot + contact management avancado)

