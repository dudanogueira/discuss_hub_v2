# Idempotency Map

Goal
- Show how dedupe keys are computed and where collisions happen.

Steps
1) Compute idempotency keys for each event.
2) List events grouped by (gateway_id, gateway_remote_id).
3) Highlight duplicates and their outcomes (created/updated/skipped).
4) Provide link to the referenced mail.message.

Outputs
- Dedupe table with collision diagnostics.
