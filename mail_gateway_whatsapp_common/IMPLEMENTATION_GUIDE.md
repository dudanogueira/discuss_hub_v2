# Mail Gateway WhatsApp Common - Implementation Guide

Este documento guia o passo a passo da implementacao. Atualize apos cada etapa.

## Objetivo
- Provider (evolution/quepasa/waha/notificame) normaliza payload e chama o common.
- Common aplica regras e escreve no Odoo (contato, canal, mensagem, status, reacao, delete).
- Discuss apenas consome os registros.

## Principios
- Modulo simples, sem acoplamento com provider.
- Idempotencia por id externo (message_id / reaction_target_id).
- Sem efeitos colaterais no provider.
- Context flags para evitar loop de outbound.

## Decisoes (manter atualizado)
- OCA padrao: usar mail.gateway + mail.notification para id externo e status. (ok)
- Contato: usar mail.guest por padrao e promover para res.partner quando vincular. (ok)
- Eventos canonicos no common: message.upsert, message.status, reaction.upsert, reaction.delete, message.delete. (ok)
- Channel: channel_type=gateway seguindo OCA (sem tipo whatsapp). (ok)

## NormalizedPayload (contrato v0)
- event: message.upsert | message.status | reaction.upsert | reaction.delete | message.delete
- provider, instance
- message_id, chat_id, from_me, timestamp
- chat_name, chat_description, chat_picture_url
- sender_jid, sender_name
- text, attachments (lista de {name, datas, mimetype})
- quote_id, quote_text
- reaction, reaction_target_id
- status, status_raw
- raw

## Etapas (implementar e testar uma a uma)
- [x] Etapa 0 - validar contrato do DTO e nomes de eventos
  - Saida: dto.to_dict consistente no log de webhook
  - Teste: replay no devtools nao quebra
- [x] Etapa 1 - message.upsert (texto simples)
  - Resolver contato (guest/partner) e canal por chat_id
  - Criar mail.message com id externo
  - Idempotencia por message_id
  - Teste: replay nao duplica
- [ ] Etapa 2 - reply/quote
  - Mapear quote_id -> parent_id quando existir
  - Teste: mensagem aparece encadeada
- [ ] Etapa 3 - attachments (image/video/audio/document)
  - Criar ir.attachment + discuss.voice.metadata para audio
  - Teste: arquivo abre no discuss
- [ ] Etapa 4 - reaction.upsert / reaction.delete
  - Vincular reacao ao autor correto
  - Teste: reacao aparece e some
- [ ] Etapa 5 - message.status
  - Atualizar status (sent/delivered/read/failed)
  - Teste: replay nao duplica status
- [ ] Etapa 6 - message.delete
  - Marcar mensagem como apagada (nao apagar registro)
  - Teste: corpo indica apagado

## Observacoes
- Manter o common independente de API externa.
- Preferir alteracoes pequenas e validar em cada etapa.
