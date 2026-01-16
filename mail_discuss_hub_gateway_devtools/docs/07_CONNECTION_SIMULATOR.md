# Connection Simulator

Goal
- Generate synthetic events to test flow without the provider.

Steps
1) Pick an event template (message, edit, delete, reaction, status).
2) Fill required fields and optional overrides.
3) Submit to the same pipeline as real webhooks.
4) Log results to compare with expected output.

Outputs
- Simulated webhook log + created records.
