# AGENTS.md - mail_discuss_hub_helpdesk_mgmt

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Sincronizar `mail.discuss.team` com `helpdesk.ticket.team`.

## Dependencias

- `mail_discuss_hub`
- `helpdesk_mgmt`

## Arquivos principais

- `models/helpdesk_ticket_team.py` (campo discuss_team_id + sync)
- `models/mail_discuss_team.py` (campo helpdesk_team_id + sync)
- `views/helpdesk_ticket_team_views.xml`

## Regras

- Sync deve ser bidirecional.
- Use context flags para evitar loop:
  - `mail_discuss_hub_sync_from_helpdesk`
  - `mail_discuss_hub_sync_from_discuss`
