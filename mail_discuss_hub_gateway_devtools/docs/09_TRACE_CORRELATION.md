# Trace Correlation

Goal
- Track a single event from webhook to all created records.

Config flag
- `mail_discuss_hub_gateway_devtools.trace_correlation_enabled`

Steps
1) Pick a webhook log.
2) Match by direct link (gateway_webhook_log_id) or by (gateway_id, gateway_remote_id).
3) Resolve channel/guest from messages or payload.
4) Review the correlation notes.

Outputs
- Correlation summary with linked messages/channels.
