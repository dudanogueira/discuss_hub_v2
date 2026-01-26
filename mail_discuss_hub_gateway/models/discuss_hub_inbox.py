# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DiscussHubInbox(models.Model):
    _inherit = "discuss.hub.inbox"

    inbox_type = fields.Selection(
        selection_add=[("gateway", "Gateway")],
        default="gateway",
    )
    gateway_id = fields.Many2one(
        "mail.gateway",
        string="Gateway",
        ondelete="cascade",
    )
    gateway_type = fields.Selection(
        related="gateway_id.gateway_type",
        readonly=False,
        store=True,
    )
    token = fields.Char(related="gateway_id.token", readonly=False)
    integrated_webhook_state = fields.Selection(
        related="gateway_id.integrated_webhook_state",
        readonly=True,
    )
    can_set_webhook = fields.Boolean(
        related="gateway_id.can_set_webhook",
        readonly=True,
    )
    webhook_url = fields.Char(related="gateway_id.webhook_url", readonly=True)
    webhook_key = fields.Char(related="gateway_id.webhook_key", readonly=False)
    webhook_secret = fields.Char(related="gateway_id.webhook_secret", readonly=False)
    webhook_user_id = fields.Many2one(
        related="gateway_id.webhook_user_id",
        readonly=False,
    )
    has_new_channel_security = fields.Boolean(
        related="gateway_id.has_new_channel_security",
        readonly=False,
    )
    company_id = fields.Many2one(
        related="gateway_id.company_id",
        store=True,
        readonly=False,
    )
    access_group_id = fields.Many2one(
        related="gateway_id.access_group_id",
        readonly=True,
    )
    discuss_team_ids = fields.Many2many(
        related="gateway_id.discuss_team_ids",
        readonly=False,
    )
    discuss_agent_ids = fields.Many2many(
        related="gateway_id.discuss_agent_ids",
        readonly=False,
    )
    member_ids = fields.Many2many(
        related="gateway_id.member_ids",
        readonly=False,
    )
    outgoing_signature = fields.Boolean(
        related="gateway_id.outgoing_signature",
        readonly=False,
    )
    outgoing_signature_format = fields.Char(
        related="gateway_id.outgoing_signature_format",
        readonly=False,
    )
    reopen_archived_conversations = fields.Boolean(
        related="gateway_id.reopen_archived_conversations",
        readonly=False,
    )

    _sql_constraints = [
        (
            "discuss_hub_inbox_gateway_unique",
            "unique(gateway_id)",
            "Gateway inbox must be unique.",
        )
    ]

    @api.constrains("inbox_type", "gateway_id")
    def _check_gateway_required(self):
        for record in self:
            if record.inbox_type == "gateway" and not record.gateway_id:
                raise ValidationError(_("Gateway is required for gateway inboxes."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("inbox_type") == "gateway" and vals.get("gateway_id") and not vals.get("name"):
                gateway = self.env["mail.gateway"].browse(vals["gateway_id"])
                vals["name"] = gateway.name
        records = super().create(vals_list)
        for record in records.filtered(lambda r: r.inbox_type == "gateway" and r.gateway_id):
            if record.name != record.gateway_id.name:
                record.gateway_id.sudo().write({"name": record.name})
                record.sudo().write({"name": record.gateway_id.name})
        return records

    def write(self, vals):
        result = super().write(vals)
        if "name" in vals or "gateway_id" in vals:
            for record in self.filtered(lambda r: r.inbox_type == "gateway" and r.gateway_id):
                if record.name != record.gateway_id.name:
                    record.gateway_id.sudo().write({"name": record.name})
                    record.sudo().write({"name": record.gateway_id.name})
        return result

    def action_set_webhook(self):
        for record in self:
            if record.gateway_id:
                record.gateway_id.set_webhook()

    def action_update_webhook(self):
        for record in self:
            if record.gateway_id:
                record.gateway_id.update_webhook()

    def action_remove_webhook(self):
        for record in self:
            if record.gateway_id:
                record.gateway_id.remove_webhook()
