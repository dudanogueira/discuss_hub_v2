# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api


def _get_general_channel_ids(env):
    general = env.ref("mail.channel_all_employees", raise_if_not_found=False)
    if general:
        return [general.id]
    return env["discuss.channel"].search([("name", "=", "general")]).ids


env = env(context=dict(env.context, mail_notrack=True, tracking_disable=True))

general_ids = _get_general_channel_ids(env)

print("Cleanup discuss data")
print("  keep general channel IDs:", general_ids or "-")

member_model = env["discuss.channel.member"]
channel_model = env["discuss.channel"]
reaction_model = env["mail.message.reaction"]
guest_model = env["mail.guest"]
message_model = env["mail.message"]

member_count = member_model.search_count([])
member_model.search([]).unlink()
print("  deleted discuss.channel.member:", member_count)

channel_domain = [("id", "not in", general_ids)] if general_ids else []
channel_count = channel_model.search_count(channel_domain)
channel_model.search(channel_domain).unlink()
print("  deleted discuss.channel (excluding general):", channel_count)

reaction_count = reaction_model.search_count([])
reaction_model.search([]).unlink()
print("  deleted mail.message.reaction:", reaction_count)

guest_count = guest_model.search_count([])
guest_model.search([]).unlink()
print("  deleted mail.guest:", guest_count)

message_domain = [("model", "=", "discuss.channel")]
message_count = message_model.search_count(message_domain)
message_model.search(message_domain).unlink()
print("  deleted mail.message (model=discuss.channel):", message_count)

env.cr.commit()
