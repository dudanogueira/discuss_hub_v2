# AGENTS.md - mail_discuss_hub

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Modulo core com:
- Menus de configuracao do Discuss
- Pagina de Settings dedicada para Discuss (replica das configs de Mensagens)
- Modelo base `mail.discuss.team`

## Dependencias

- `mail` (Odoo core).

## Arquivos principais

- `__manifest__.py`
- `views/mail_discuss_hub_menus.xml` - menus de administracao
- `views/mail_discuss_team_views.xml` - views e action de Teams
- `views/res_config_settings_views.xml` - pagina Settings do Discuss
- `security/ir.model.access.csv`
- `models/discuss_team.py`
- `models/mail_message.py` - ajuste de author store
- `models/res_config_settings.py` - campos de configuracao

## Regras

- Nao colocar regras de integracao aqui.
- Qualquer integracao deve ir para addons dedicados.
