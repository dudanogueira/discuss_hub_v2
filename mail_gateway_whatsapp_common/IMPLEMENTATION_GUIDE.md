# Mail Gateway WhatsApp Common - Implementation Guide

Este documento guia o passo a passo da implementacao. Atualize apos cada etapa.

## Objetivo
- Provider (evolution/quepasa/waha/notificame) normaliza payload e chama o common.
- Common aplica regras e escreve no Odoo (contato, canal, mensagem, status, reacao, delete).
- Outbound: common normaliza a saida do Odoo e delega o envio ao provider.
- Discuss apenas consome os registros.

## Principios
- Modulo simples, sem acoplamento com provider.
- Common e o unico ponto de conexao entre Odoo e providers (inbound e outbound).
- Devtools e opcional e nunca pode ser dependencia de modulo algum.
- Idempotencia por id externo (message_id / reaction_target_id).
- Sem efeitos colaterais no provider.
- Context flags para evitar loop de outbound.

## Decisoes (manter atualizado)
- OCA padrao: usar mail.gateway + mail.notification para id externo e status. (ok)
- Contato: usar mail.guest por padrao e promover para res.partner quando vincular. (ok)
- Eventos canonicos no common: message.upsert, message.status, reaction.upsert, reaction.delete, message.delete, contact.update, chat.update. (ok)
- Channel: channel_type=gateway seguindo OCA (sem tipo whatsapp). (ok)
- Outbound usa OutboundPayload e providers implementam apenas `_send_outbound` (sem escrever no Odoo). (ok)

## NormalizedPayload (contrato v0)
- event: message.upsert | message.status | reaction.upsert | reaction.delete | message.delete | contact.update | chat.update
- provider, instance
- message_id, chat_id, is_group, from_me, timestamp
- chat_name, chat_description, chat_picture_url, chat_unread_count
- sender_jid, sender_name, sender_participant_jid
- contact_jid, contact_name, contact_profile_pic_url
- text, attachments (lista de {name, datas, mimetype})
- text_is_html (true apenas quando provider gerar HTML confiavel, ex: link de localizacao)
- quote_id, quote_text
- reaction, reaction_target_id
- status, status_raw
- raw

## OutboundPayload (contrato v0)
- provider, gateway_type
- notification_id, message_id
- chat_id, instance
- text, author_name
- attachments (lista de {id, name, mimetype, size, datas})

## Etapas (implementar e testar uma a uma)
- [x] Etapa 0 - validar contrato do DTO e nomes de eventos
  - Saida: dto.to_dict consistente no log de webhook
  - Teste: replay no devtools nao quebra
- [x] Etapa 1 - message.upsert (texto simples)
  - Resolver contato (guest/partner) e canal por chat_id
  - Criar mail.message com id externo
  - Idempotencia por message_id
  - Teste: replay nao duplica
- [x] Etapa 2 - reply/quote
  - Mapear quote_id -> parent_id quando existir
  - Teste: mensagem aparece encadeada
- [x] Etapa 3 - attachments (image/video/audio/document)
  - Criar ir.attachment + discuss.voice.metadata para audio
  - Teste: arquivo abre no discuss
- [x] Etapa 4 - reaction.upsert / reaction.delete
  - Vincular reacao ao autor correto
  - Disparar `_bus_send_reaction_group` para atualizar UI
  - Teste: reacao aparece e some
- [x] Etapa 5 - message.status
  - Atualizar status (sent/delivered/read/failed)
  - Teste: replay nao duplica status
- [x] Etapa 6 - message.delete
  - Marcar mensagem como apagada (nao apagar registro)
  - Teste: corpo indica apagado
- [x] Etapa 7 - outbound (texto/anexos)
  - mail.notification.send_gateway roteia para o common
  - common cria OutboundPayload e delega `_send_outbound` do provider
  - provider envia para API externa; common atualiza mail.message/mail.notification
- [x] Etapa 8 - outbound reactions (UI)
  - Override de `_message_reaction` no common para enviar reaction ao provider
  - Provider Evolution usa `/message/sendReaction`

## Observacoes
- Manter o common independente de API externa.
- Preferir alteracoes pequenas e validar em cada etapa.
- Attachments devem ser enviados ao message_post como bytes (nao base64).
- Audio deve incluir info={"voice": True} para gerar discuss.voice.metadata.
- Outbound: `_get_outbound_provider` retorna recordset vazio; nao usar `bool(recordset)` para validar suporte.
