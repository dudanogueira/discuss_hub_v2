======================
Mail Discuss Hub Core
======================

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

This module provides the Discuss Hub core models and settings only.
Administration menus moved to the optional
``mail_discuss_hub_gateway_devtools`` addon.

**Table of contents**

.. contents::
   :local:

Overview
========

Provides:

- Discuss Hub settings (res.config.settings integration).
- Discuss Teams model and views.
- Security/access rules for the core entities.

Does not provide:

- Messages/Guests/Channels admin menus (devtools only).
- Webhook logs, replay, or cleanup tools (devtools only).

Dependencies
============

- ``mail`` (`Odoo mail <https://github.com/odoo/odoo/tree/18.0/addons/mail>`_)

Configuration
=============

No extra configuration is required.

Usage
=====

For administration menus, install ``mail_discuss_hub_gateway_devtools`` and
use Settings > Discuss > Messages.

Roadmap (TODO)
==============

- Add more Discuss configuration shortcuts.
- Expand Discuss Teams management features (routing, tags, assignments).
- Improve admin documentation for message management.

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
