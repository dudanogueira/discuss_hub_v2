# Gap Checklist

Goal
- Track received webhook events that are not implemented yet.

Config flag
- `mail_discuss_hub_gateway_devtools.gap_checklist_enabled`

Where to use
- Devtools -> Webhooks -> Gap Checklist

How it works
1) Maintain a list of supported events per provider (devtools only).
2) Normalize incoming event names (`lower`, `_` -> `.`).
3) Compare webhook logs against supported events.
4) Aggregate gaps by gateway + event, showing count and last seen.
5) Attach TODO references for known gaps.

Current support map (Evolution)
- Supported events: `messages.upsert`, `send.message`
- Known events list is loaded from `mail.gateway.whatsapp_evolution_api.webhook_event` when available.
- TODO refs are prefilled for the most common missing events.

Outputs
- Gap report with priorities, last log link, and TODO reference.

Notes
- The checklist only reads logs; it does not change data.
- Use the provider filter to avoid mixing different gateway types.
