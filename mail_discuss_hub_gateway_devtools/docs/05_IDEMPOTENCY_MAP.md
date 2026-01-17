# Idempotency Map

Status
- Disabled in devtools while the common model is being implemented.
- The current pipeline does not persist remote IDs on `mail.message`, so the map
  would be misleading until `mail.notification.gateway_message_id` and reaction
  keys are consistently stored.
