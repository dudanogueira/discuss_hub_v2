================
Mail Gateway Fix
================

This module fixes the cache key used by ``mail.gateway._get_gateway_map``
by scoping it to ``state`` and ``gateway_type``.

It also restores a ``Request.charset`` property removed in Werkzeug 3,
used by the ``mail_gateway`` webhook controller to decode payloads.

Dependencies
============

- ``mail_gateway`` (OCA/social)
