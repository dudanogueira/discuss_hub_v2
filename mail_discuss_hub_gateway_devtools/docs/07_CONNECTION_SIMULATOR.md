# Connection Simulator

Goal
- Generate synthetic events to test flow without the provider.

Config flag
- `mail_discuss_hub_gateway_devtools.connection_simulator_enabled`

Steps
1) Pick an event template (message, status, delete, reaction).
2) Fill required fields and optional overrides.
3) Generate a synthetic payload and log it as a webhook entry.
4) Optionally process the payload through the pipeline.

Outputs
- Simulated webhook log and, when processed, created/updated records.
