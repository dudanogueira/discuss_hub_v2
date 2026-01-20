================
Mail Gateway Fix
================

This module fixes the cache key used by ``mail.gateway._get_gateway_map``
by scoping it to ``state`` and ``gateway_type``.

Dependencies
============

- ``mail_gateway`` (OCA/social)
