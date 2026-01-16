from odoo import models


class MailGatewayWhatsappCommon(models.AbstractModel):
    _name = "mail.gateway.whatsapp.common"
    _description = "WhatsApp Gateway Common"
    _abstract = True

    def _process_normalized(self, gateway, dto, channel, author=None):
        """Placeholder: common processing to be implemented step-by-step."""
        return {
            "status": "noop",
            "gateway_id": gateway.id if gateway else False,
        }
