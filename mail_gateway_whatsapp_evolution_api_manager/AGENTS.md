# AGENTS.md - mail_gateway_whatsapp_evolution_api_manager

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Gerenciar servidores e instancias da Evolution API.
Este modulo nao altera o gateway diretamente.

## Dependencias

- `mail_gateway_whatsapp_evolution_api`

## Arquivos principais

- `models/evolution_api_server.py`
- `models/evolution_api_instance.py`
- `views/evolution_api_server_views.xml`
- `views/evolution_api_instance_views.xml`
- `views/evolution_api_menus.xml`
- `security/ir.model.access.csv`

## Observacoes

- Os campos de Settings ficam em `evolution.api.instance` e atualizam a API via `/settings/set/{instance}`.
- Consulte `EVOLUTION_API_REFERENCE.md` para metodos/payloads.
- Divergencias entre doc/modulos/servidor devem ser reconferidas e atualizadas no guia.
