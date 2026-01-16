# Unified Timeline

Goal
- Show a single chronological view from webhook to Odoo records per channel/guest.

Steps
1) Pick a discuss.channel or mail.guest.
2) Load related webhook logs by chat_id/jid.
3) Join with normalized payloads and created records.
4) Render a timeline: webhook -> normalized -> mail.message.

Outputs
- Timeline list with timestamps and links to records.
