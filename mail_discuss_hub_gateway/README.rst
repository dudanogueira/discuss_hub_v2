==========================
Mail Discuss Hub Gateway
==========================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-lcsztl%2Fdiscuss_hub-lightgray.png?logo=github
    :target: https://github.com/lcsztl/discuss_hub
    :alt: lcsztl/discuss_hub

|badge1| |badge2| |badge3|

This module provides Discuss utilities and admin tooling for gateway
integrations and fixes to the core OCA Model.

**Table of contents**

.. contents::
   :local:

Overview
========

Main features:

- Group gateway threads by instance in the Discuss sidebar.
- Improve author behavior for gateway messages (guest management and
  partner opening).
- Extend "Manage guest" to reuse existing links, update phone, and
  rename gateway channels.
- Add a webhook audit log model and menu.

Dependencies
============

- ``mail_gateway`` (`OCA/social mail_gateway <https://github.com/OCA/social/tree/18.0/mail_gateway>`_)
- ``mail_discuss_hub`` (`lcsztl/discuss_hub <https://github.com/lcsztl/discuss_hub>`_)

Configuration
=============

No extra configuration is required. Ensure the user belongs to the
"Gateway / User" group to access gateway data.

Usage
=====

- Discuss > Configuration > Messages:
  - Gateway
  - Gateway Partner Channels
  - Webhook Logs
- Click on gateway message authors to manage guests or open partners.

Roadmap (TODO)
==============

- Add team-based routing rules for gateway messages.
- Provide assignment strategies per Discuss Team.
- Add filters and retention policies for webhook logs.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/lcsztl/discuss_hub/issues>`_.
In case of trouble, please check there if your issue has already been reported.

Credits
=======

Authors
-------

* Soloz Techonologies <lucas.zotelli@soloz.com.br>

Maintainers
-----------

This module is maintained by Lucas Zotelli.

This module is part of the `lcsztl/discuss_hub <https://github.com/lcsztl/discuss_hub>`_
project on GitHub.
