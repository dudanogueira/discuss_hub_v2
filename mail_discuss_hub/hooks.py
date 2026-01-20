# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID


DISCUSS_CHANNEL_DOMAIN = """
[
    "|",
        "&",
            ("channel_type", "=", "gateway"),
            ("discuss_team_id", "!=", False),
            ("discuss_team_id.access_group_id", "in", user.groups_id.ids),
        "|",
            "&",
            ("channel_type", "not in", ["channel", "gateway"]),
            ("is_member", "=", True),
            "&",
                ("channel_type", "=", "channel"),
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
"""

DISCUSS_CHANNEL_MEMBER_READ_DOMAIN = """
[
    "|",
        "&",
            ("channel_id.channel_type", "=", "gateway"),
            ("channel_id.discuss_team_id", "!=", False),
            ("channel_id.discuss_team_id.access_group_id", "in", user.groups_id.ids),
        "|",
            "&",
                ("channel_id.channel_type", "not in", ["channel", "gateway"]),
                ("channel_id.is_member", "=", True),
            "&",
                ("channel_id.channel_type", "=", "channel"),
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
"""


def _update_rule_domain(env, xmlid, domain):
    rule = env.ref(xmlid, raise_if_not_found=False)
    if not rule:
        return
    if rule.domain_force != domain:
        rule.sudo().write({"domain_force": domain})


def _ensure_team_access_groups(env):
    teams = env["mail.discuss.team"].with_context(active_test=False).search([])
    teams._sync_access_group()


def post_init_hook(env):
    env = env(user=SUPERUSER_ID, context={**env.context, "active_test": False})
    _ensure_team_access_groups(env)
    _update_rule_domain(env, "mail.ir_rule_discuss_channel_all", DISCUSS_CHANNEL_DOMAIN)
    _update_rule_domain(
        env, "mail.ir_rule_discuss_channel_member_read_all", DISCUSS_CHANNEL_MEMBER_READ_DOMAIN
    )
