# Controlled Replay

Goal
- Replay webhook logs with throttling and overrides to reproduce bugs.

Config flag
- `mail_discuss_hub_gateway_devtools.controlled_replay_enabled`

Steps
1) Filter webhook logs by date/event/chat_id.
2) Select replay order (original, reverse, custom).
3) Configure throttle (ms delay between events).
4) Apply overrides (timestamp, from_me, sender_jid).
5) Execute replay and log outcomes.

Outputs
- Replay run summary (success/fail).
- Per-event status and created records.
