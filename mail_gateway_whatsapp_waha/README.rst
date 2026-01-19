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

.. note::
   WAHA Core supports only the ``default`` session. For multiple sessions,
   WAHA Plus is required.

Usage
=====

Use Discuss to send text messages. Inbound webhooks and media sending are not
implemented yet.

Roadmap (TODO)
==============

- Support inbound webhooks (NormalizedPayload -> common).
- Support media/attachments and status updates.

Credits
=======

Authors
-------

* Soloz Technologies

Maintainers
-----------

This module is maintained by the Discuss Hub team.
