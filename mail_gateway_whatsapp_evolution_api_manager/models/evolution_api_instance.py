# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EvolutionApiInstance(models.Model):
    _name = "evolution.api.instance"
    _description = "Evolution API Instance"
    _inherit = ["mail.gateway.whatsapp_evolution_api.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    server_id = fields.Many2one(
        "evolution.api.server",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        related="server_id.company_id",
        store=True,
        readonly=True,
    )
    connection_status = fields.Char(readonly=True)
    status = fields.Selection(
        [
            ("connected", "Connected"),
            ("connecting", "Connecting"),
            ("disconnected", "Disconnected"),
            ("unknown", "Unknown"),
        ],
        compute="_compute_status",
        store=True,
        readonly=True,
        default="unknown",
    )
    profile_name = fields.Char(readonly=True)
    phone_number = fields.Char(readonly=True)
    api_key = fields.Char(readonly=True)
    last_sync = fields.Datetime(readonly=True)
    raw_payload = fields.Text(readonly=True)
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

    def _apply_settings(self):
        self.ensure_one()
        if not self.server_id:
            raise UserError(_("Evolution API server is required."))
        if not self.name:
            raise UserError(_("Instance name is required."))
        payload = self._settings_payload()
        self._evolution_api_set_settings(
            self.server_id.base_url,
            self.api_key or self.server_id.api_key,
            self.name,
            payload,
        )

    def write(self, vals):
        settings_fields = {
            "reject_calls",
            "ignore_groups",
            "always_online",
            "read_messages",
            "sync_full_history",
            "read_status",
        }
        res = super().write(vals)
        if settings_fields.intersection(vals):
            for record in self:
                try:
                    record._apply_settings()
                except UserError as exc:
                    raise UserError(_("Failed to update Evolution settings: %s") % exc) from exc
        return res

    _sql_constraints = [
        (
            "evolution_api_instance_unique",
            "unique(server_id, name)",
            "Instance name must be unique per server.",
        ),
    ]

    @api.depends("connection_status")
    def _compute_status(self):
        for record in self:
            record.status = self._map_status(record.connection_status)

    @staticmethod
    def _map_status(connection_status):
        if not connection_status:
            return "unknown"
        if connection_status == "open":
            return "connected"
        if connection_status in ("connecting", "pair_device", "qrcode"):
            return "connecting"
        if connection_status in ("close", "closed", "disconnected"):
            return "disconnected"
        return "unknown"
