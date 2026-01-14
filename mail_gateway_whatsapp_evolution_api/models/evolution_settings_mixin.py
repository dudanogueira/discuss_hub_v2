# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EvolutionApiSettingsMixin(models.AbstractModel):
    _name = "mail.gateway.whatsapp_evolution_api.settings.mixin"
    _description = "Evolution API settings mixin"

    reject_calls = fields.Boolean(
        string="Reject Calls",
        help="Reject all incoming calls.",
    )
    ignore_groups = fields.Boolean(
        string="Ignore Groups",
        help="Ignore all messages from groups.",
    )
    always_online = fields.Boolean(
        string="Always Online",
        help="Keep the WhatsApp always online.",
    )
    read_messages = fields.Boolean(
        string="Read Messages",
        help="Mark all messages as read.",
    )
    sync_full_history = fields.Boolean(
        string="Sync Full History",
        help="Sync all complete chat history on scan QR code.",
    )
    read_status = fields.Boolean(
        string="Read Status",
        help="Mark all statuses as read.",
    )

    def _get_settings_fields(self):
        return {
            "reject_calls",
            "ignore_groups",
            "always_online",
            "read_messages",
            "sync_full_history",
            "read_status",
        }

    def _settings_payload(self):
        self.ensure_one()
        return {
            "rejectCall": self.reject_calls,
            "groupsIgnore": self.ignore_groups,
            "alwaysOnline": self.always_online,
            "readMessages": self.read_messages,
            "syncFullHistory": self.sync_full_history,
            "readStatus": self.read_status,
        }
