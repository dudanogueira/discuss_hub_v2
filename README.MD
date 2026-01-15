# Discuss Hub

Addons locais para Odoo focados em Discuss + integrações (Gateway, WhatsApp Evolution API, CRM, Helpdesk).

## Usage

- Copie/monte este diretório em um `addons_path` do Odoo.
- No Odoo: `Apps` → `Update Apps List`.
- Instale os módulos desejados.

### Integrações (CRM / Helpdesk)

Os módulos de integração foram desenhados para integrar o Discuss Hub ao CRM/Helpdesk de forma mais ampla.
No momento, a implementação cobre o **link manual** entre equipes (sem criar automaticamente durante o uso normal),
servindo como base para funcionalidades adicionais que ainda serão desenvolvidas.

Exceção (bootstrap na instalação, focado em equipes):

- Ao **instalar** o addon [mail_discuss_hub_crm](mail_discuss_hub_crm/), se já existirem equipes em `CRM → Teams`, o módulo cria automaticamente uma equipe equivalente em `Discuss Hub → Discuss Teams` e faz o vínculo.
- Ao **instalar** o addon [mail_discuss_hub_helpdesk_mgmt](mail_discuss_hub_helpdesk_mgmt/), se já existirem equipes em `Helpdesk → Teams`, o módulo cria automaticamente uma equipe equivalente em `Discuss Hub → Discuss Teams` e faz o vínculo.

Notas:

- Essa rotina roda **uma única vez** no momento da instalação (post-init hook). Ela **não** roda em upgrade.
- Esse bootstrap é restrito a equipes e não representa toda a integração com o módulo.
- Ao adicionar novos campos Python, é necessário **reiniciar o serviço do Odoo** para o registry carregar o código antes de atualizar/instalar o módulo.

## Addons

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------

addon | version | summary
----- | ------- | -------
[mail_discuss_hub](mail_discuss_hub/) | 18.0.1.0.0 | Discuss configuration menus for message administration
[mail_discuss_hub_gateway](mail_discuss_hub_gateway/) | 18.0.1.0.0 | Discuss gateway extensions and sidebar grouping utilities
[mail_gateway_whatsapp_evolution_api](mail_gateway_whatsapp_evolution_api/) | 18.0.1.0.0 | Gateway integration for WhatsApp via Evolution API
[mail_gateway_whatsapp_evolution_api_manager](mail_gateway_whatsapp_evolution_api_manager/) | 18.0.1.0.0 | Manage Evolution API servers and instances
[mail_discuss_hub_crm](mail_discuss_hub_crm/) | 18.0.1.0.0 | CRM integration for Discuss Hub (teams + roadmap)
[mail_discuss_hub_helpdesk_mgmt](mail_discuss_hub_helpdesk_mgmt/) | 18.0.1.0.0 | Helpdesk Mgmt integration for Discuss Hub (teams + roadmap)

[//]: # (end addons)

## Credits

### Authors

- Soloz Technologies

### Based on / Inspired by

Este projeto foi desenvolvido com base em conceitos, código e inspiração dos seguintes projetos open-source:

| Projeto | Autor | Repositório |
| ------- | ----- | ----------- |
| Discuss Hub | DiscussHub Team | https://github.com/discusshub/discuss_hub |
| WA Conn | Diego Rodrigues | https://github.com/diegofrodrigues/wa_conn |
| Odoo WhatsApp Evolution API | Gerencial P | https://github.com/gerencialp-bit/odoo-whatsapp-evolution-api |

Agradecemos a todos os autores e contribuidores desses projetos por disponibilizarem seu trabalho sob licenças open-source.
## License

AGPL-3 (veja o `__manifest__.py` de cada addon).
