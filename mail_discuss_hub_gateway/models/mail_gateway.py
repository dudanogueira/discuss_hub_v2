# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MailGateway(models.Model):
    _inherit = "mail.gateway"

    discuss_team_ids = fields.Many2many(
        "mail.discuss.team",
        string="Discuss Teams",
        help="Teams allowed to handle this inbox.",
    )
    access_group_id = fields.Many2one(
        "res.groups",
        string="Gateway Access Group",
        readonly=True,
        help="Access group managed automatically for this gateway.",
    )

    def _get_access_group_name(self):
        self.ensure_one()
        return f"Gateway: {self.name}"

    def _ensure_access_group(self):
        self.ensure_one()
        if self.access_group_id:
            return self.access_group_id
        vals = {"name": self._get_access_group_name()}
        category = self.env.ref(
            "mail_gateway.module_category_gateway", raise_if_not_found=False
        )
        if category:
            vals["category_id"] = category.id
        group = self.env["res.groups"].sudo().create(vals)
        self.sudo().with_context(
            mail_discuss_hub_gateway_skip_group_sync=True
        ).write({"access_group_id": group.id})
        return group

    def _sync_access_group(self):
        for gateway in self:
            group = gateway._ensure_access_group()
            desired_name = gateway._get_access_group_name()
            if group.name != desired_name:
                group.sudo().with_context(
                    mail_discuss_hub_gateway_skip_group_sync=True
                ).write({"name": desired_name})

    def _sync_channels_access_group(self):
        channel_model = self.env["discuss.channel"].sudo()
        for gateway in self:
            group_id = gateway.access_group_id.id if gateway.access_group_id else False
            channels = channel_model.search([("gateway_id", "=", gateway.id)])
            if channels:
                channels.write({"group_public_id": group_id})

    @api.model_create_multi
    def create(self, vals_list):
        gateways = super().create(vals_list)
        gateways._sync_access_group()
        gateways._sync_channels_access_group()
        return gateways

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get("mail_discuss_hub_gateway_skip_group_sync"):
            if "name" in vals:
                self._sync_access_group()
        if "access_group_id" in vals:
            self._sync_channels_access_group()
        return result

    def unlink(self):
        groups = self.mapped("access_group_id")
        result = super().unlink()
        if groups:
            remaining = self.env["mail.gateway"].with_context(active_test=False).search(
                [("access_group_id", "in", groups.ids)]
            )
            groups_to_remove = groups - remaining.mapped("access_group_id")
            if groups_to_remove:
                groups_to_remove.sudo().unlink()
        return result
