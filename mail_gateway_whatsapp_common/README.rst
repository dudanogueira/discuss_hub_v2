Mail Gateway WhatsApp Common
============================

Camada comum para gateways WhatsApp nao-oficiais (Evolution, WAHA, Quepasa,
NotificaMe). Define o DTO `NormalizedPayload` e um servico compartilhado
(`mail.gateway.whatsapp.common`) que os providers devem chamar apos normalizar
seus webhooks.

Principais pontos
-----------------

- Campos em ``mail.message`` para id externo, chat id, status, quote, reaction,
  payload bruto (para auditoria) e constraint de idempotencia por gateway.
- DTO `NormalizedPayload` cobre texto/caption, midia (base64 ou anexos), quote,
  reaction, status e metadados (provider, instance, chat, timestamp, raw).
- Servico `_process_normalized` trata eventos canonicos:
  - ``message_upsert``: cria/atualiza mensagem com idempotencia.
  - ``message_status``: progride status (sent→delivered→read).
  - ``message_delete``: marca como deletada.
  - ``reaction_upsert`` / ``reaction_delete``: aplica/remover reacao.
- Providers so precisam mapear o webhook bruto para o DTO e informar
  channel/author; o comum cuida do restante.

Como usar em um provider
------------------------

1. Dependencia do módulo: adicionar ``mail_gateway_whatsapp_common``.
2. No webhook: construir um `NormalizedPayload` (ex.: `NormalizedPayload(...)`).
3. Chamar ``self.env["mail.gateway.whatsapp.common"]._process_normalized(gateway, dto, channel, author)``.
4. Manter a logica de resolucao de canal/author dentro do provider (cada API tem
   sua forma).
