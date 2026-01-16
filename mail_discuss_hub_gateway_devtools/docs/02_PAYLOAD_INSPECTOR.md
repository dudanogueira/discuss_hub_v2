# Payload Inspector

Goal
- Provide schema validation, field usage, and diffs between similar payloads.

Steps
1) Select a webhook log (mail.gateway.webhook.log).
2) Parse and pretty-print JSON with field paths.
3) Validate required fields per provider/event.
4) Highlight fields used by mapping vs ignored fields.
5) Compare two payloads (same event) with diff view.

Outputs
- Validation status (ok/warn/error).
- Used fields list.
- Missing required fields list.
- Diff report for troubleshooting changes.
