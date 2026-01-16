# Provider Comparator

Goal
- Compare the same event across providers (Evolution, WAHA, etc.).

Config flag
- `mail_discuss_hub_gateway_devtools.provider_comparator_enabled`

Steps
1) Pick two webhook logs.
2) Normalize both using adapters when available.
3) Diff the normalized outputs.
4) Review field differences and notes.

Outputs
- Side-by-side normalized diff with notes.
