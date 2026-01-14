# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID


def post_init_hook(env):
    """On install, create/link Discuss Teams for existing Helpdesk Teams.

    This is a one-time migration helper meant to bootstrap installations where
    helpdesk teams already exist before the integration module is installed.
    """

    # env is an odoo.api.Environment (no .sudo()); switch to superuser explicitly.
    env = env(user=SUPERUSER_ID, context={**env.context, "active_test": False})

    HelpdeskTeam = env["helpdesk.ticket.team"]
    DiscussTeam = env["mail.discuss.team"]

    for helpdesk_team in HelpdeskTeam.search([("discuss_team_id", "=", False)]):
        members = helpdesk_team.user_ids
        if helpdesk_team.user_id:
            members |= helpdesk_team.user_id

        # Create the Discuss Team already linked to the Helpdesk Team.
        # Keep the sync context to avoid triggering bidirectional sync during install,
        # but still set the explicit link field.
        discuss_team = DiscussTeam.with_context(
            mail_discuss_hub_sync_from_helpdesk=True
        ).create(
            {
                "name": helpdesk_team.name,
                "active": helpdesk_team.active,
                "company_id": helpdesk_team.company_id.id,
                "user_id": helpdesk_team.user_id.id if helpdesk_team.user_id else False,
                "member_ids": [(6, 0, members.ids)],
                "color": helpdesk_team.color,
                "helpdesk_team_id": helpdesk_team.id,
            }
        )

        # Link from the Helpdesk side (without sync_from_discuss) so the Helpdesk
        # write logic can ensure the reciprocal link is consistent.
        helpdesk_team.write({"discuss_team_id": discuss_team.id})
