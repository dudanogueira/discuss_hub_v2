# Provider Comparator

Goal
- Compare the same event across providers (Evolution, WAHA, etc.).

Steps
1) Load a pair of payloads for the same event.
2) Normalize both using the adapters.
3) Diff the NormalizedPayload outputs.
4) Flag fields that require provider-specific handling.

Outputs
- Side-by-side normalized diff and action notes.
