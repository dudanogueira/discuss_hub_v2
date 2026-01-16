# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class CleanupWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.cleanup_wizard"
    _description = "Cleanup Discuss/Gateway Data (dev tool)"

    clear_members = fields.Boolean(default=True)
    clear_channels = fields.Boolean(default=True, help="Exclui canais (exceto general).")
    clear_reactions = fields.Boolean(default=True)
    clear_guests = fields.Boolean(default=True)
    clear_messages = fields.Boolean(default=True, help="Somente mensagens de discuss.channel.")

    def action_cleanup(self):
        self.ensure_one()
        # Placeholder seguro: evita limpeza destrutiva sem passo a passo revisado.
        raise UserError(
            _(
                "Limpeza destrutiva não habilitada neste wizard. "
                "Implemente com cautela e use apenas em ambiente de desenvolvimento."
            )
        )
