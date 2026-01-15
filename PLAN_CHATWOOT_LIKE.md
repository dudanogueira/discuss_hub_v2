# Plano Chatwoot-like (Inbox por Time)

Objetivo
- Fazer o Discuss se comportar como Chatwoot: inbox por time, atribuicao, fila de nao atribuida, filtros por time e futuras acoes em contexto (lead/cotacao) sem exigir membership para visibilidade.

Principios
- Manter OCA/OCB intocados; extender apenas por addons locais.
- Comecar minimo (visibilidade + atribuicao) e crescer por etapas.
- Preferir dominio/filtro no backend; JS apenas para UX e listas dinamicas.
- Deixar toda logica nova opt-in via feature flag.

Arquitetura (macro)
- Dados: adicionar campos de time/atribuicao no discuss.channel (ou modelo ponte).
- Acesso: permitir leitura por membros do time mesmo sem membership do canal.
- UI: adicionar Inbox no Discuss com filtros (Minhas, Todas, Nao atribuida, Time).
- Atribuicao: ao atribuir, adicionar membership real apenas para o assignee.

Addons propostos (responsabilidade)
- mail_discuss_hub_inbox
  - Campos no discuss.channel.
  - Metodos de atribuicao e mudanca de estado.
  - Hooks de roteamento gateway -> time.
  - Regras de acesso por time.
- mail_discuss_hub_inbox_ui
  - Patches OWL no Discuss (sidebar + listas).
  - Contadores dinamicos e filtros.
  - Acoes inline (atribuir/desatribuir).
- mail_discuss_hub_inbox_crm (futuro)
  - Acoes para criar lead/cotacao a partir da conversa.
  - Contexto (partner, phone, gateway, mensagem).

Fase 0 - Decisoes e baseline
- Modelo de ownership:
  - discuss.channel.discuss_team_id (M2O mail.discuss.team)
  - discuss.channel.assigned_user_id (M2O res.users)
  - discuss.channel.assignment_state (unassigned, assigned, closed)
- Roteamento:
  - mail.gateway.discuss_team_id (time por gateway) ou regras de roteamento.
- Visibilidade:
  - membros do time podem ler canais e mensagens sem membership.

Fase 1 - Modelo de dados + acesso
- Campos no discuss.channel:
  - discuss_team_id
  - assigned_user_id
  - assignment_state
  - last_gateway_message_at (opcional para ordenacao)
- Campo no gateway:
  - mail.gateway.discuss_team_id
- Regras de acesso:
  - discuss.channel: read para membros do time.
  - mail.message: read por time quando canal tem discuss_team_id.
  - write restrito ao assignee ou lider do time.
- Feature flag:
  - parametro de sistema ou flag no mail.discuss.team.

Fase 2 - Roteamento + workflow de atribuicao
- Ao criar canal via gateway:
  - setar discuss_team_id pelo gateway
  - assignment_state = unassigned
- Acoes:
  - action_assign_to_me
  - action_assign_to_user
  - action_unassign
  - action_set_state
- Membership:
  - ao atribuir, adicionar membership so para o assignee
  - ao desatribuir, remover membership (opcional)

Fase 3 - Inbox UI (Discuss)
- Sidebar "Inbox" com filtros:
  - Minhas (assigned to me)
  - Todas (team channels)
  - Nao atribuida
  - Time (selector)
- Contadores via read_group; lista via search_read.
- Acoes inline: atribuir/desatribuir, abrir thread.
- Manter discuss atual para thread/composer.

Fase 4 - UX e refinamentos
- Tags/estagios (opcional):
  - Inspirar em wa_conn.
  - Manter MVP leve.
- Ordenacao:
  - last_gateway_message_at ou last_message_date.
- Estado visual:
  - badges (unassigned/assigned/closed).
  - mostrar time e assignee.

Fase 5 - Acoes dentro da conversa (futuro)
- Painel lateral ou botoes:
  - Criar Lead, Criar Cotacao, Log de atividade.
- Contexto pre-preenchido:
  - partner_id, phone, channel name, gateway metadata.
- Abrir em modal para manter o fluxo.

Fase 6 - Automacao + SLA (futuro)
- Auto-atribuicao:
  - round-robin por time
  - regras por gateway/contato
- SLA:
  - primeiro response, tempo de resolucao
- Auditoria:
  - historico de atribuicoes

Diretrizes tecnicas
- Evitar adicionar todos os membros do time no canal.
- Usar record rules para visibilidade; write limitado.
- Indexar discuss_team_id e assigned_user_id.
- Patches JS pequenos e isolados.
- Migracao opcional para canais existentes.

Riscos e mitigacoes
- Regras de acesso em mail.message sao sensiveis; testar leitura por time.
- Patches de Discuss sao sensiveis a upgrades; manter minimal.
- Listas grandes: paginacao e read_group.

Marcos
- M1: Modelo + acesso + roteamento no gateway.
- M2: Atribuicao server side + filtros basicos.
- M3: UI polish + contadores + performance.
- M4: Acoes CRM em contexto.
