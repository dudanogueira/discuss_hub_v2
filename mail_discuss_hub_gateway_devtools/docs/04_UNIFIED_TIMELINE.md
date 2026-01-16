# Unified Timeline

Goal
- Show a single chronological view of webhook logs and related Odoo messages per channel/guest.

Config flag
- `mail_discuss_hub_gateway_devtools.unified_timeline_enabled`

Steps
1) Pick a discuss.channel or mail.guest.
2) Load related webhook logs by gateway + chat token (remoteJid).
3) Load related mail.message records for the channel.
4) Render a unified timeline ordered by timestamp.

Outputs
- Timeline list with timestamps and links to webhook logs and messages.
