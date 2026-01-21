# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrRule(models.Model):
    _inherit = "ir.rule"

    @api.model
    def _apply_discuss_hub_gateway_rules(self):
        domains = {
            "mail.ir_rule_discuss_channel_all": """
                [
                    "|",
                        "&",
                            ("channel_type", "not in", ("channel", "gateway")),
                            ("is_member", "=", True),
                        "&",
                            ("channel_type", "in", ("channel", "gateway")),
                            "|",
                                "&",
                                    ("parent_channel_id", "=", False),
                                    "|",
                                        ("group_public_id", "=", False),
                                        ("group_public_id", "in", user.groups_id.ids),
                                "&",
                                    ("parent_channel_id", "!=", False),
                                    "|",
                                        ("parent_channel_id.group_public_id", "=", False),
                                        ("parent_channel_id.group_public_id", "in", user.groups_id.ids),
                ]
            """,
            "mail.ir_rule_discuss_channel_member_is_self_all": """
                [
                    ("is_self", "=", True),
                    "|",
                        ("channel_id.channel_type", "not in", ("channel", "gateway")),
                        "|",
                            "&",
                                ("channel_id.parent_channel_id", "=", False),
                                "|",
                                    ("channel_id.group_public_id", "=", False),
                                    ("channel_id.group_public_id", "in", user.groups_id.ids),
                            "&",
                                ("channel_id.parent_channel_id", "!=", False),
                                "|",
                                    ("channel_id.parent_channel_id.group_public_id", "=", False),
                                    ("channel_id.parent_channel_id.group_public_id", "in", user.groups_id.ids),
                ]
            """,
            "mail.ir_rule_discuss_channel_member_read_all": """
                [
                    "|",
                        "&",
                            ("channel_id.channel_type", "not in", ("channel", "gateway")),
                            ("channel_id.is_member", "=", True),
                        "&",
                            ("channel_id.channel_type", "in", ("channel", "gateway")),
                            "|",
                                "&",
                                    ("channel_id.parent_channel_id", "=", False),
                                    "|",
                                        ("channel_id.group_public_id", "=", False),
                                        ("channel_id.group_public_id", "in", user.groups_id.ids),
                                "&",
                                    ("channel_id.parent_channel_id", "!=", False),
                                    "|",
                                        ("channel_id.parent_channel_id.group_public_id", "=", False),
                                        ("channel_id.parent_channel_id.group_public_id", "in", user.groups_id.ids),
                ]
            """,
            "mail.ir_rule_discuss_channel_member_create_is_group_matching_all": """
                [
                    ("is_self", "=", True),
                    ("channel_id.channel_type", "in", ("channel", "gateway")),
                    "|",
                        ("channel_id.group_public_id", "=", False),
                        ("channel_id.group_public_id", "in", user.groups_id.ids)
                ]
            """,
            "mail.ir_rule_discuss_channel_member_create_is_group_matching_group_user": """
                [
                    ("is_self", "=", False),
                    ("channel_id.channel_type", "in", ("channel", "gateway")),
                    "|",
                        ("channel_id.group_public_id", "=", False),
                        ("channel_id.group_public_id", "in", user.groups_id.ids)
                ]
            """,
            "mail.ir_rule_discuss_channel_member_create_is_member_group_user": """
                [
                    ("is_self", "=", False),
                    ("channel_id.channel_type", "not in", ("channel", "chat", "gateway")),
                    ("channel_id.is_member", "=", True)
                ]
            """,
        }
        for xmlid, domain in domains.items():
            rule = self.env.ref(xmlid, raise_if_not_found=False)
            if rule:
                rule.write({"domain_force": domain.strip()})
