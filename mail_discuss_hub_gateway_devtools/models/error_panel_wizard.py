# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import csv
import io
import json

from odoo import _, fields, models
from odoo.exceptions import UserError


class ErrorPanelWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.error_panel_wizard"
    _description = "Error Panel (dev tool)"

    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    date_from = fields.Datetime(string="From")
    date_to = fields.Datetime(string="To")
    direction = fields.Selection(
        [("in", "Inbound"), ("out", "Outbound")], string="Direction"
    )
    include_http_errors = fields.Boolean(string="Include HTTP Errors", default=True)
    include_processing_errors = fields.Boolean(
        string="Include Processing Errors", default=True
    )
    min_http_status = fields.Integer(string="Min HTTP Status", default=400)
    line_ids = fields.One2many(
        "mail_discuss_hub_dev.error_panel_line",
        "wizard_id",
        string="Lines",
    )

    def action_build(self):
        self.ensure_one()
        if not self._is_enabled():
            raise UserError(_("Error panel is disabled by Devtools settings."))

        self.line_ids.unlink()
        lines = self._build_lines()
        line_model = self.env["mail_discuss_hub_dev.error_panel_line"]
        for values in lines:
            values["wizard_id"] = self.id
            line_model.create(values)

        return {
            "type": "ir.actions.act_window",
            "name": _("Error Panel"),
            "res_model": "mail_discuss_hub_dev.error_panel_line",
            "view_mode": "list,form",
            "target": "current",
            "domain": [("wizard_id", "=", self.id)],
            "context": {"default_wizard_id": self.id},
        }

    def action_export_json(self):
        self.ensure_one()
        content = json.dumps(self._export_lines(), ensure_ascii=True, indent=2)
        return self._create_export_attachment("error_panel.json", content, "application/json")

    def action_export_csv(self):
        self.ensure_one()
        output = io.StringIO()
        fieldnames = [
            "gateway",
            "endpoint",
            "event",
            "error_class",
            "count",
            "last_seen",
            "http_status_sample",
            "error_message_sample",
            "log_ids",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for line in self.line_ids:
            writer.writerow(
                {
                    "gateway": line.gateway_id.display_name if line.gateway_id else "",
                    "endpoint": line.endpoint or "",
                    "event": line.event or "",
                    "error_class": line.error_class or "",
                    "count": line.count,
                    "last_seen": line.last_seen or "",
                    "http_status_sample": line.http_status_sample or "",
                    "error_message_sample": line.error_message_sample or "",
                    "log_ids": ",".join(str(item.id) for item in line.log_ids),
                }
            )
        return self._create_export_attachment(
            "error_panel.csv", output.getvalue(), "text/csv"
        )

    def _create_export_attachment(self, filename, content, mimetype):
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": filename,
                    "type": "binary",
                    "datas": base64.b64encode(content.encode("utf-8")),
                    "mimetype": mimetype,
                }
            )
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=1",
            "target": "self",
        }

    def _export_lines(self):
        return [
            {
                "gateway": line.gateway_id.display_name if line.gateway_id else "",
                "endpoint": line.endpoint or "",
                "event": line.event or "",
                "error_class": line.error_class or "",
                "count": line.count,
                "last_seen": line.last_seen,
                "http_status_sample": line.http_status_sample,
                "error_message_sample": line.error_message_sample or "",
                "log_ids": [log.id for log in line.log_ids],
            }
            for line in self.line_ids
        ]

    def _build_lines(self):
        grouped = {}
        for log in self._fetch_logs():
            if not self._is_error_log(log):
                continue
            key = (log.gateway_id.id, log.endpoint or "", log.event or "", self._error_class(log))
            entry = grouped.setdefault(
                key,
                {
                    "gateway_id": log.gateway_id.id if log.gateway_id else False,
                    "endpoint": log.endpoint or "",
                    "event": log.event or "",
                    "error_class": self._error_class(log),
                    "log_ids": [],
                    "count": 0,
                    "last_seen": False,
                    "http_status_sample": log.http_status or 0,
                    "error_message_sample": log.error_message or "",
                },
            )
            entry["log_ids"].append(log.id)
            entry["count"] += 1
            if not entry["last_seen"] or (log.create_date and log.create_date > entry["last_seen"]):
                entry["last_seen"] = log.create_date
            if not entry["error_message_sample"] and log.error_message:
                entry["error_message_sample"] = log.error_message
            if not entry["http_status_sample"] and log.http_status:
                entry["http_status_sample"] = log.http_status

        lines = []
        for entry in grouped.values():
            lines.append(
                {
                    "gateway_id": entry["gateway_id"],
                    "endpoint": entry["endpoint"],
                    "event": entry["event"],
                    "error_class": entry["error_class"],
                    "count": entry["count"],
                    "last_seen": entry["last_seen"],
                    "http_status_sample": entry["http_status_sample"],
                    "error_message_sample": entry["error_message_sample"],
                    "log_ids": [(6, 0, entry["log_ids"])],
                }
            )
        return lines

    def _fetch_logs(self):
        domain = []
        if self.gateway_id:
            domain.append(("gateway_id", "=", self.gateway_id.id))
        if self.direction:
            domain.append(("direction", "=", self.direction))
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("create_date", "<=", self.date_to))
        return self.env["mail.gateway.webhook.log"].sudo().search(domain)

    def _is_error_log(self, log):
        http_error = self.include_http_errors and (log.http_status or 0) >= self.min_http_status
        processing_error = self.include_processing_errors and (
            log.status == "error" or bool(log.error_message)
        )
        return http_error or processing_error

    def _error_class(self, log):
        message = log.error_message or ""
        if ":" in message:
            return message.split(":", 1)[0].strip()
        if "\n" in message:
            return message.split("\n", 1)[0].strip()
        return message.strip() or "HTTP"

    def _is_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.error_panel_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")


class ErrorPanelLine(models.TransientModel):
    _name = "mail_discuss_hub_dev.error_panel_line"
    _description = "Error Panel Line (dev tool)"

    wizard_id = fields.Many2one(
        "mail_discuss_hub_dev.error_panel_wizard",
        required=True,
        ondelete="cascade",
    )
    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    endpoint = fields.Char()
    event = fields.Char()
    error_class = fields.Char()
    count = fields.Integer()
    last_seen = fields.Datetime()
    http_status_sample = fields.Integer()
    error_message_sample = fields.Text()
    log_ids = fields.Many2many(
        "mail.gateway.webhook.log",
        "mail_discuss_hub_dev_error_log_rel",
        "line_id",
        "log_id",
        string="Webhook Logs",
    )
