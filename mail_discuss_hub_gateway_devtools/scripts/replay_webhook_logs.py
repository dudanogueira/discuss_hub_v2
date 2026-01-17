# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import os
import time

from odoo import fields


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name, default=0):
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name, default=0.0):
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_csv(name):
    value = os.getenv(name) or ""
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items


def _env_datetime(name):
    value = os.getenv(name)
    if not value:
        return False
    return fields.Datetime.to_datetime(value)


def _extract_instance_name(payload):
    if not isinstance(payload, dict):
        return False
    for key in ("instance", "instanceName", "instance_name"):
        value = payload.get(key)
        if value:
            return value
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("instance", "instanceName", "instance_name"):
            value = data.get(key)
            if value:
                return value
    return False


def _extract_server_url(payload):
    if not isinstance(payload, dict):
        return False
    for key in ("server_url", "serverUrl", "serverURL"):
        value = payload.get(key)
        if value:
            return value
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("server_url", "serverUrl", "serverURL"):
            value = data.get(key)
            if value:
                return value
    return False


def _resolve_gateway(log, payload, fallback_gateway_id):
    if fallback_gateway_id:
        gateway = env["mail.gateway"].browse(fallback_gateway_id)
        return gateway if gateway.exists() else False
    if log.gateway_id:
        return log.gateway_id
    endpoint = log.endpoint or ""
    parts = [part for part in endpoint.split("/") if part]
    if "gateway" not in parts:
        usage = False
        token = False
    else:
        idx = parts.index("gateway")
        if len(parts) <= idx + 2:
            usage = False
            token = False
        else:
            usage = parts[idx + 1]
            token = parts[idx + 2]
    if usage and token:
        gateway = env["mail.gateway"].search(
            [("gateway_type", "=", usage), ("webhook_key", "=", token)],
            limit=1,
        )
        if gateway:
            return gateway
    instance_name = _extract_instance_name(payload)
    if not instance_name:
        return False
    domain = [
        ("gateway_type", "=", "whatsapp_evolution_api"),
        ("evolution_instance", "=", instance_name),
    ]
    server_url = _extract_server_url(payload)
    gateways = env["mail.gateway"].search(domain)
    if server_url:
        server_url = server_url.rstrip("/")
        gateways = gateways.filtered(
            lambda g: (g.evolution_api_url or "").rstrip("/") == server_url
        )
    if gateways:
        return gateways[:1]
    return env["mail.gateway"].search(
        [
            ("gateway_type", "=", "whatsapp_evolution_api"),
            ("name", "=", instance_name),
        ],
        limit=1,
    )


def _latest_message_for_log(log_id):
    return (
        env["mail.message"]
        .sudo()
        .search([("gateway_webhook_log_id", "=", log_id)], order="id desc", limit=1)
    )


ctx = dict(env.context, mail_notrack=True, tracking_disable=True)
env = env(context=ctx)

direction = os.getenv("DIRECTION", "in")
gateway_id = _env_int("GATEWAY_ID") or False
log_ids = [int(item) for item in _env_csv("LOG_IDS") if item.isdigit()]
events = [item for item in _env_csv("EVENTS") if item]
date_from = _env_datetime("DATE_FROM")
date_to = _env_datetime("DATE_TO")
limit = _env_int("LIMIT")
dry_run = _env_bool("DRY_RUN")
report_skipped = _env_bool("REPORT_SKIPPED")
max_report = _env_int("MAX_REPORT", default=50)
update_message_date = _env_bool("UPDATE_MESSAGE_DATE", default=True)
update_create_date = _env_bool("UPDATE_CREATE_DATE")
commit_every = _env_int("COMMIT_EVERY")
sleep_seconds = _env_float("SLEEP_SECONDS")

domain = [("direction", "=", direction)]
if log_ids:
    domain.append(("id", "in", log_ids))
if events:
    domain.append(("event", "in", events))
if date_from:
    domain.append(("create_date", ">=", date_from))
if date_to:
    domain.append(("create_date", "<=", date_to))
if gateway_id:
    domain.append(("gateway_id", "=", gateway_id))

logs = env["mail.gateway.webhook.log"].sudo().search(
    domain, order="create_date asc, id asc"
)
if limit:
    logs = logs[:limit]

print(
    "Replay webhook logs:",
    f"count={len(logs)}",
    f"direction={direction}",
    f"gateway_id={gateway_id or '-'}",
    f"dry_run={dry_run}",
    f"report_skipped={report_skipped}",
)

if dry_run and not report_skipped:
    raise SystemExit(0)

processed = 0
skipped = 0
errors = 0
reported = 0

for log in logs:
    payload_text = log.request_payload or ""
    if not payload_text:
        if report_skipped and reported < max_report:
            print(f"Skipped log {log.id}: empty payload")
            reported += 1
        skipped += 1
        continue
    try:
        payload = json.loads(payload_text)
    except Exception:
        if report_skipped and reported < max_report:
            print(f"Skipped log {log.id}: invalid JSON payload")
            reported += 1
        skipped += 1
        continue
    if not isinstance(payload, dict):
        if report_skipped and reported < max_report:
            print(f"Skipped log {log.id}: payload is not a JSON object")
            reported += 1
        skipped += 1
        continue

    gateway = _resolve_gateway(log, payload, gateway_id)
    if not gateway:
        if report_skipped and reported < max_report:
            print(f"Skipped log {log.id}: gateway not resolved")
            reported += 1
        skipped += 1
        continue

    dispatcher = (
        env[f"mail.gateway.{gateway.gateway_type}"]
        .with_user(gateway.webhook_user_id or env.user)
        .with_company(gateway.company_id)
        .with_context(
            mail_notrack=True,
            tracking_disable=True,
            no_gateway_notification=True,
            gateway_webhook_log_id=log.id,
        )
    )
    kwargs = dict(payload) if isinstance(payload, dict) else {}
    kwargs["event"] = payload.get("event")
    kwargs["data"] = payload.get("data")
    kwargs["server_url"] = _extract_server_url(payload)
    kwargs["instance_name"] = _extract_instance_name(payload)

    try:
        dispatcher._receive_update(gateway, kwargs)
        processed += 1
    except Exception as exc:  # pylint: disable=broad-except
        errors += 1
        print(f"Error processing log {log.id}: {exc}")
    else:
        if update_message_date:
            msg = _latest_message_for_log(log.id)
            if msg:
                msg_date = log.create_date
                msg.write(
                    {
                        "date": msg_date,
                        "write_date": msg_date,
                    }
                )
                if update_create_date:
                    env.cr.execute(
                        """
                        UPDATE mail_message
                        SET create_date=%s
                        WHERE id=%s
                    """,
                        [msg_date, msg.id],
                    )
                    env.cr.execute(
                        """
                        UPDATE mail_message_res_partner_rel
                        SET create_date=%s
                        WHERE mail_message_id=%s
                    """,
                        [msg_date, msg.id],
                    )
        if commit_every and processed % commit_every == 0:
            env.cr.commit()
        if sleep_seconds:
            time.sleep(sleep_seconds)

print(
    "Done",
    f"processed={processed}",
    f"skipped={skipped}",
    f"errors={errors}",
)
