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
