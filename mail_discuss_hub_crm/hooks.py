# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID


def post_init_hook(env):
    """On install, create/link Discuss Teams for existing CRM Teams.

    This is a one-time migration helper meant to bootstrap installations where CRM
    teams already exist before the integration module is installed.
    """

    # env is an odoo.api.Environment (no .sudo()); switch to superuser explicitly.
    env = env(user=SUPERUSER_ID, context={**env.context, "active_test": False})

    CrmTeam = env["crm.team"]
    DiscussTeam = env["mail.discuss.team"]

    for crm_team in CrmTeam.search([("discuss_team_id", "=", False)]):
        members = crm_team.member_ids
        if crm_team.user_id:
            members |= crm_team.user_id

        # Create the Discuss Team already linked to the CRM Team.
        # Keep the sync context to avoid triggering bidirectional sync during install,
        # but still set the explicit link field.
        discuss_team = DiscussTeam.with_context(mail_discuss_hub_sync_from_crm=True).create(
            {
                "name": crm_team.name,
                "active": crm_team.active,
                "company_id": crm_team.company_id.id,
                "user_id": crm_team.user_id.id if crm_team.user_id else False,
                "member_ids": [(6, 0, members.ids)],
                "color": crm_team.color,
                "crm_team_id": crm_team.id,
            }
        )

        # Link from the CRM side (without sync_from_discuss) so the CRM write
        # logic can ensure the reciprocal link is consistent.
        crm_team.write({"discuss_team_id": discuss_team.id})
