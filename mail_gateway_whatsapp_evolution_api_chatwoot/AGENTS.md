# AGENTS.md - mail_gateway_whatsapp_evolution_api_chatwoot

## Leitura obrigatoria

- Leia `AGENTS.md` (raiz) e `README.rst` deste modulo antes de alterar.

## Objetivo

Sincronizar webhooks do Evolution API para o Chatwoot.

## Dependencias

- `mail_gateway_whatsapp_evolution_api`

## Regras

- Considerar este addon experimental; mantenha mudanças isoladas.
- Nao introduzir dependencias adicionais em modulos de producao.
- Respeitar a arquitetura: parse Evolution -> DTO (common) e sincronizar com Chatwoot.
