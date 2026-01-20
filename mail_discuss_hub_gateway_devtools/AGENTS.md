# AGENTS.md - mail_discuss_hub_gateway_devtools

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Ferramentas tecnicas opcionais para desenvolvimento:
- Menus de administracao em Discuss > Messages.
- Logs de webhook, replay e cleanup.
- Views de diagnostico e payloads raw (somente quando instalado).

## Dependencias

- `mail_discuss_hub`
- `mail_gateway`
- `mail_gateway_whatsapp_evolution_api_manager`

## Regras

- Nao adicionar logica de negocio aqui; apenas diagnostico e utilitarios.
- Produção nao deve depender deste modulo.
- Nao pode ser dependencia de nenhum outro modulo (devtools deve ser sempre opcional).
- Qualquer campo de debug deve ficar neste modulo (nao no core).
- Evitar fallbacks legados; projeto greenfield.
- Persistencia de logs de webhook deve respeitar a flag de configuracao
  `mail_discuss_hub_gateway_devtools.webhook_log_enabled` (Devtools > Recursos).
- Log de webhook e' injetado via override de `_receive_update` nos providers
  (somente quando o devtools esta instalado), chamando `_devtools_log_webhook`.
- Logs de envio (saida) sao adicionados via override de `_send_outbound` no provider
  quando o devtools esta instalado.
- Devtools grava `internal_result` e `internal_routine` em `mail.gateway.webhook.log`
  para diagnostico (resultado interno e rotina acionada).
- O replay limpa `internal_result`/`internal_routine` dos logs selecionados antes
  de reprocessar, para refletir o comportamento atual.
