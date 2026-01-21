Discuss Hub Addons
==================

Repositorio de addons do Discuss Hub.

Dependencias externas (OCA/social)
==================================

Este repositorio nao inclui os modulos abaixo. Para usar os gateways, baixe o
repo oficial OCA/social (branch 18.0) e adicione ao addons_path do Odoo (ou
copie apenas estes modulos):

- mail_gateway: https://github.com/OCA/social/tree/18.0/mail_gateway
- mail_gateway_whatsapp: https://github.com/OCA/social/tree/18.0/mail_gateway_whatsapp
- mail_gateway_telegram: https://github.com/OCA/social/tree/18.0/mail_gateway_telegram

Docker Compose
==================
No momento temos um arquivo docker-compose-dev.yaml para facilitar o
desenvolvimento local.

``docker compose -f compose-dev.yaml up -d odoo evolution``
