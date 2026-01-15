============================================
Mail Gateway WhatsApp Evolution API Chatwoot
============================================

This module stores Chatwoot metadata from Evolution API webhook payloads
into ``mail.message`` fields.

Features
========

- Extract ``chatwoot_message_id``, ``chatwoot_conversation_id``,
  ``chatwoot_inbox_id``, and ``chatwoot_source`` from
  ``gateway_webhook_log_id.request_payload``.

Configuration
=============

- Install with ``mail_discuss_hub_gateway`` and
  ``mail_gateway_whatsapp_evolution_api``.
- No additional settings are required.

Roadmap (TODO)
==============

- Add links from gateway channels/messages to Chatwoot conversations.
- Sync message status/read events back to Chatwoot.
- Map Chatwoot inbox metadata to Odoo gateways.
- Enrich partners using Chatwoot contact data.

Credits
=======

Authors
-------

* Soloz Technologies

Maintainers
-----------

This module is maintained by the Discuss Hub team.
