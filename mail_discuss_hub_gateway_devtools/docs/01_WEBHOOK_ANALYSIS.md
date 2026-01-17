# Devtools Webhook Analysis - Step by Step

Goal
- Provide a single screen to inspect raw webhook payloads side-by-side with the normalized output and the resulting Odoo records.

Config flag
- `mail_discuss_hub_gateway_devtools.webhook_analysis_enabled`

Main screen (two-column layout)
Left column: Raw Event
- Webhook log metadata (created_at, direction, http_status, endpoint, gateway, instance).
- Raw payload (pretty JSON).
- Hash/fingerprint for quick dedupe checks.

Right column: Normalized + Result
- NormalizedPayload (pretty JSON).
- Field Map table (raw_path -> normalized_field -> destination + routine).
- Created/updated records:
  - discuss.channel
  - mail.guest / res.partner
  - mail.message
  - mail.message.reaction
- Idempotency keys and match decisions.

Step-by-step flow to display
1) Select a webhook log (mail.gateway.webhook.log).
2) Parse and render the raw payload (left column).
3) Run the provider adapter (Evolution/WAHA/...) in "dry-run" mode.
4) Capture the NormalizedPayload (right column).
5) Apply mapping rules and show:
   - matched channel + why (chat_id, gateway_id, instance, etc.)
   - matched sender + why (jid/phone/name, guest vs partner)
6) Show idempotency check:
   - message_id (mail.notification.gateway_message_id)
   - chat_id (discuss.channel.gateway_channel_token)
   - result: created / updated / skipped
7) Show record write preview (before/after diff).
8) Provide "Replay" action with override options.

Mapping table (example format)
- data.key.remoteJid -> chat_id -> discuss.channel.gateway_channel_token
- data.pushName -> sender_name -> mail.guest.name
- data.message.text -> text -> mail.message.body
- data.key.id -> message_id -> mail.notification.gateway_message_id
 - event -> routine -> receive_message / send_message / delete_message / update_status

Controls
- Replay with overrides (force from_me, change timestamp, swap sender).
- Compare with previous/next log (same chat_id).
- Export as JSON (raw + normalized + mapping).

Notes
- This is dev-only. No business logic here.
- Adapters should expose a debug hook to return NormalizedPayload + mapping metadata without side effects.
