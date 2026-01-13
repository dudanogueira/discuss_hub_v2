=====================
Mail Discuss Hub CRM
=====================

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

This module links CRM teams to Discuss teams for future routing and
assignment strategies.

**Table of contents**

.. contents::
   :local:

Overview
========

Adds a Discuss Team field on CRM Teams and keeps teams synchronized
between CRM and Discuss.

Dependencies
============

- ``mail_discuss_hub`` (`lcsztl/discuss_hub <https://github.com/lcsztl/discuss_hub>`_)
- ``crm`` (`Odoo CRM <https://github.com/odoo/odoo/tree/18.0/addons/crm>`_)

Configuration
=============

No extra configuration is required.

Usage
=====

Open CRM Team and set the "Discuss Team" field. Team changes are
synchronized between CRM and Discuss.

Roadmap (TODO)
==============

- Auto-assign leads/opportunities to Discuss Teams.
- Extend routing rules based on CRM stages or tags.
- Define routing rules based on CRM stages or tags.

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
