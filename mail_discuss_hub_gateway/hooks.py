# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID


def post_init_hook(env):
    env = env(user=SUPERUSER_ID, context={**env.context, "active_test": False})
    channel_model = env["discuss.channel"]
    gateway_model = env["mail.gateway"]

    for gateway in gateway_model.search([]):
        group_id = (
            gateway.discuss_team_id.access_group_id.id
            if gateway.discuss_team_id and gateway.discuss_team_id.access_group_id
            else False
        )
        channels = channel_model.search([("gateway_id", "=", gateway.id)])
        if not channels:
            continue
        channels.write(
            {
                "discuss_team_id": gateway.discuss_team_id.id or False,
                "group_public_id": group_id,
            }
        )
