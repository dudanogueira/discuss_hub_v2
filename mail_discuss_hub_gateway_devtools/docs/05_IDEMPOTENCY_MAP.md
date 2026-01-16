# Idempotency Map

Goal
- Show how dedupe keys are computed and where collisions happen.

Config flag
- `mail_discuss_hub_gateway_devtools.idempotency_map_enabled`

Steps
1) Pick filters (gateway/date range) and build the map.
2) Group webhook logs and mail.message by (gateway_id, gateway_remote_id).
3) Flag collisions when the same key appears more than once.
4) Open a line to see related logs and messages.

Outputs
- Dedupe table with collision diagnostics and linked records.
