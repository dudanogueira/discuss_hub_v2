# Plano de split do mail_discuss_hub_gateway

Objetivo
- Separar "fixes" de comportamento do core mail_gateway das funcionalidades de UX/integracao.
- Ganhar clareza (bugfix vs feature) e permitir reuso de fixes em outros projetos.

Motivacao
- Hoje o mail_discuss_hub_gateway mistura:
  - ajustes de comportamento (fixes)
  - infraestrutura de observabilidade (webhook log)
  - UX no Discuss (sidebar, aba Messages, menus)
- Separar reduz acoplamento e facilita manutencao.

Estado atual (2026-01): o modelo/observabilidade de webhook foi movido para
`mail_discuss_hub_devtools` para manter os modulos de producao limpos.

Modulos alvo (proposta minima)

1) mail_gateway_fixes
- Escopo: ajustes de comportamento para gateways.
- Conteudo:
  - models/mail_guest_manage.py
  - static/src/js/message_author_fix.esm.js
- Dependencias sugeridas:
  - mail_gateway (e mail)
- Assets:
  - web.assets_backend com message_author_fix.esm.js

2) mail_gateway_webhook_log (infra/observabilidade)
- Escopo: modelo de log e extensoes de mail.message para auditoria.
- Conteudo:
  - models/mail_gateway_webhook_log.py
  - models/mail_message.py (gateway_webhook_* fields)
  - security/security.xml + security/ir.model.access.csv
  - views/mail_gateway_webhook_log.xml
  - views/mail_message_views.xml
  - scripts/replay_webhook_logs.py (opcional, pode ficar aqui)
- Dependencias sugeridas:
  - mail_gateway (grupo gateway_user, gateway_id)
  - mail (mail.message)
- Menus:
  - nao expor menu aqui (deixar para mail_discuss_hub_gateway),
    apenas action + views.

3) mail_discuss_hub_gateway (UX Discuss)
- Escopo: UX e navegacao no Discuss para gateways.
- Conteudo:
  - static/src/js/gateway_instance_sidebar.esm.js
  - views/discuss_channel_views.xml (aba Messages)
  - views/mail_discuss_hub_gateway_menus.xml (menus de config)
- Dependencias sugeridas:
  - mail_discuss_hub
  - mail_gateway
  - mail_gateway_webhook_log (para usar action do log)
- Opcional:
  - depende de mail_gateway_fixes se quiser carregar os fixes sempre.

Mapeamento de arquivos (origem -> destino)
- mail_discuss_hub_gateway/models/mail_guest_manage.py
  -> mail_gateway_fixes/models/mail_guest_manage.py
- mail_discuss_hub_gateway/static/src/js/message_author_fix.esm.js
  -> mail_gateway_fixes/static/src/js/message_author_fix.esm.js
- mail_discuss_hub_gateway/models/mail_gateway_webhook_log.py
  -> mail_gateway_webhook_log/models/mail_gateway_webhook_log.py
- mail_discuss_hub_gateway/models/mail_message.py
  -> mail_gateway_webhook_log/models/mail_message.py
- mail_discuss_hub_gateway/security/*
  -> mail_gateway_webhook_log/security/*
- mail_discuss_hub_gateway/views/mail_gateway_webhook_log.xml
  -> mail_gateway_webhook_log/views/mail_gateway_webhook_log.xml
- mail_discuss_hub_gateway/views/mail_message_views.xml
  -> mail_gateway_webhook_log/views/mail_message_views.xml
- mail_discuss_hub_gateway/scripts/replay_webhook_logs.py
  -> mail_gateway_webhook_log/scripts/replay_webhook_logs.py (opcional)
- mail_discuss_hub_gateway/static/src/js/gateway_instance_sidebar.esm.js
  -> manter em mail_discuss_hub_gateway
- mail_discuss_hub_gateway/views/discuss_channel_views.xml
  -> manter em mail_discuss_hub_gateway
- mail_discuss_hub_gateway/views/mail_discuss_hub_gateway_menus.xml
  -> manter em mail_discuss_hub_gateway

Impacto em dependencias (exemplos)
- mail_gateway_whatsapp_evolution_api
  - hoje usa log se existir (opcional). Pode continuar opcional.
  - se quiser obrigar logs, adicionar dependencia em mail_gateway_webhook_log.
- mail_gateway_whatsapp_evolution_api_chatwoot
  - usa gateway_webhook_log_id e related fields.
  - deve depender de mail_gateway_webhook_log (e nao mais de mail_discuss_hub_gateway).

Migracao e compatibilidade
- Modelo mail.gateway.webhook.log nao muda, apenas muda de modulo.
- Views/actions/menus terao novos external IDs.
  - Necessario migrar ir_model_data (module) para evitar duplicar registros.
- Estrategia:
  - criar script de migracao (pre-migrate) para atualizar
    ir_model_data.module dos registros movidos.
  - manter xml_ids consistentes (mesmo nome, novo modulo).

Etapas sugeridas (execucao)
1) Criar os novos addons com __manifest__, __init__, README.
2) Mover arquivos conforme mapeamento.
3) Ajustar assets (JS) nos manifests novos.
4) Ajustar dependencias nos manifests atuais.
5) Atualizar referencias de action/view/menu (xml refs).
6) Criar migracao de ir_model_data (module rename).
7) Atualizar docs (README e AGENTS).
8) Upgrade sequencial dos modulos no Odoo.

Checklist de validacao
- Webhook log continua aparecendo em Discuss > Config.
- Aba Messages em discuss.channel continua acessivel.
- Click em autor de mensagem gateway abre Manage guest / partner.
- JS sidebar de instancias continua funcionando.
- Chatwoot module ainda consegue ler gateway_webhook_* fields.

Riscos e mitigacoes
- Duplicacao de menus/views por external ID novo.
  - Mitigar com migracao ir_model_data.
- Dep tree maior.
  - Manter split minimo e dependencias claras.
- JS assets nao carregarem.
  - Garantir manifests e assets_backend corretos.
