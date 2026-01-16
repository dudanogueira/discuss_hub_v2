# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class WebhookReplayWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.webhook_replay_wizard"
    _description = "Replay Webhook Logs (dev tool)"

    direction = fields.Selection(
        [("in", "Inbound"), ("out", "Outbound")],
        default="in",
        required=True,
    )
    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    events = fields.Char(
        help="Opcional: lista separada por vírgula de eventos para filtrar (ex: MESSAGES_UPSERT)."
    )
    date_from = fields.Datetime(string="Date from")
    date_to = fields.Datetime(string="Date to")
    limit = fields.Integer(default=0, help="0 para sem limite")
    dry_run = fields.Boolean(default=False, help="Se marcado, apenas relata contagem.")
    commit_every = fields.Integer(default=0, help="0 para não commitar parcial.")
    sleep_seconds = fields.Float(default=0.0, help="Delay opcional entre reprocessamentos.")

    def action_replay(self):
        self.ensure_one()
        # Placeholder seguro: evita rodar reprocessamento automático sem implementação revisada.
        raise UserError(
            _(
                "Implementar lógica de replay aqui. Use este wizard apenas em ambiente de "
                "desenvolvimento/controlado."
            )
        )
