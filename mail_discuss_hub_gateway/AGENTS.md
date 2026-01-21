# AGENTS.md - mail_discuss_hub_gateway

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Integrações Discuss + mail_gateway (UI e regras comuns de canais gateway).

## Dependencias

- `mail_gateway`
- `mail_gateway_whatsapp_common`
- `mail_discuss_hub`

## Arquivos principais

- `static/src/js/gateway_instance_sidebar.esm.js`
- `models/discuss_channel.py` (propaga time do gateway para o canal)
- `models/mail_gateway.py` (campo discuss_team_id no gateway)
- `models/mail_gateway_abstract.py` (cria canal sem membros em massa)
- `models/mail_gateway_whatsapp_common.py` (cria canal sem membros em massa)
- `views/mail_gateway_views.xml` (campo do time no form do gateway)
- `hooks.py` (backfill group_public_id e discuss_team_id em canais existentes)

## Regras

- Nao alterar OCA diretamente.
- Manter o modulo focado em regras genericas de gateway.
- Canais gateway nao devem adicionar membros automaticamente (apenas autor/guest).
- Canais gateway devem herdar `group_public_id` do time para controle de acesso.
- TODO: Avaliar constraint em `discuss.channel.member` para bloquear usuarios internos fora do `group_public_id` em canais gateway, considerando bypass para guests/autores e promocao de visitante -> contato.
