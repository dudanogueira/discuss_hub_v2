# AGENTS.md - mail_gateway_whatsapp_evolution_api

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Gateway WhatsApp via Evolution API.

## Dependencias

- `mail_gateway` (OCA).
- `mail_gateway_whatsapp_common` (servico/DTO compartilhado).

## Pontos importantes

- O webhook URL deve ter db fixo no `odoo.conf`.
- Nao usar `?db=` (Evolution API nao preserva querystring).
- Nao adicionar campos em `mail.guest` neste modulo (extensoes devem ficar no common).
- Parseia o payload bruto em `NormalizedPayload` e delega a `mail_gateway_whatsapp_common` para criar/atualizar mensagens.
- Common e o unico ponto de conexao com o Odoo; este modulo nao escreve no Odoo.
- Outbound e' roteado pelo common; este modulo so implementa `_send_outbound` (API externa).
- Consulte `EVOLUTION_API_REFERENCE.md` para metodos/payloads.
- Divergencias entre doc/modulos/servidor devem ser reconferidas e atualizadas no guia.
- Persistencia de logs de webhook e' controlada pela flag
  `mail_discuss_hub_gateway_devtools.webhook_log_enabled` (Devtools > Recursos)
  e acontece via override de `_receive_update` no devtools, chamando
  `_devtools_log_webhook` quando disponivel.
- Status do webhook: `processed` apenas quando `_process_normalized` retorna `ok` ou `duplicate`;
  caso contrario fica `received` (sem acao no Odoo).
- Devtools e opcional e nunca deve ser dependencia de modulo algum.
- Enriquecimento de grupos: o provider consulta a Evolution API apenas quando o
  payload nao traz `subject/desc/picture` e o canal local esta incompleto
  (nome fallback, nome igual ao sender, descricao ou imagem vazias). A consulta
  so acontece em `message.upsert`.
- Campos de id no webhook (Evolution):
  - `messages.upsert`: `data.key.remoteJid` (jid), `data.key.remoteJidAlt` (pode ser `@lid`),
    `data.key.participant` (pode ser `@lid`) e `data.key.participantAlt` (jid quando presente).
  - `messages.update`: `data.remoteJid` pode vir como `@lid`.
  - `contacts.update`/`chats.*`: `data.remoteJid` ou `data[0].remoteJid` (jid).
  - `connection.update`: `data.wuid` (jid).
- Prioridade de sender JID: preferir JIDs com `@s.whatsapp.net`/`@c.us`, depois `@lid`,
  e por ultimo `@g.us`. Isso evita salvar `@lid` quando existe `participantAlt` valido.

## Arquivos principais

- `models/mail_gateway.py` (campos Evolution e defaults)
- `models/mail_gateway_whatsapp_evolution_api.py` (integra API)
- `views/mail_gateway_evolution.xml`
