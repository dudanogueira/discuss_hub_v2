==========================
Mail Gateway WhatsApp WAHA
==========================

This module integrates Odoo Mail Gateway with WAHA to send WhatsApp messages.

**Table of contents**

.. contents::
   :local:

Overview
========

Features:

- Configure WAHA API URL and session.
- Send outbound text messages from Discuss.
- Receive inbound text messages via WAHA webhooks.
- Inbound/outbound flows are routed through ``mail_gateway_whatsapp_common``;
  this module only adapts WAHA payloads.

Dependencies
============

- ``mail_gateway`` (`OCA/social mail_gateway <https://github.com/OCA/social/tree/18.0/mail_gateway>`_)
- ``mail_gateway_whatsapp_common`` (servico/DTO compartilhado)

Configuration
=============

1. Open Settings > Discuss > Messages > Gateway.
2. Create a gateway with type "WhatsApp (WAHA)".
3. Set the WAHA API URL and session.
4. Use the Gateway ``token`` field as the WAHA API key.
5. Click **Update Webhook** to register the WAHA webhook for the session.

.. note::
   If ``webhook_secret`` is set, WAHA will sign webhooks with
   ``X-Webhook-Hmac`` (SHA-256) and Odoo will verify it.

.. note::
   WAHA Core supports only the ``default`` session. For multiple sessions,
   WAHA Plus is required.

Usage
=====

Use Discuss to send text messages. Inbound webhooks are handled for text
messages (media is ignored for now). O devtools e opcional e nunca pode ser
dependencia de nenhum modulo.

Roadmap (TODO)
==============

- Support media/attachments and status updates.
- Add reaction and ack handling.

Credits
=======

Authors
-------

* Soloz Technologies

Maintainers
-----------

This module is maintained by the Discuss Hub team.
