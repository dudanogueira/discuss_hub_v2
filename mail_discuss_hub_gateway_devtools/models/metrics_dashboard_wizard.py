# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class MetricsDashboardWizard(models.TransientModel):
    _name = "mail_discuss_hub_dev.metrics_dashboard_wizard"
    _description = "Metrics Dashboard (dev tool)"

    gateway_id = fields.Many2one("mail.gateway", string="Gateway")
    date_from = fields.Datetime(string="From")
    date_to = fields.Datetime(string="To")
    line_ids = fields.One2many(
        "mail_discuss_hub_dev.metrics_dashboard_line",
        "wizard_id",
        string="Metrics",
    )

    def action_build(self):
        self.ensure_one()
        if not self._is_enabled():
            raise UserError(_("Metrics dashboard is disabled by Devtools settings."))

        self.line_ids.unlink()
        metrics = self._compute_metrics()
        line_model = self.env["mail_discuss_hub_dev.metrics_dashboard_line"]
        for item in metrics:
            item["wizard_id"] = self.id
            line_model.create(item)

        return {
            "type": "ir.actions.act_window",
            "name": _("Metrics Dashboard"),
            "res_model": "mail_discuss_hub_dev.metrics_dashboard_line",
            "view_mode": "list,form",
            "target": "current",
            "domain": [("wizard_id", "=", self.id)],
            "context": {"default_wizard_id": self.id},
        }

    def _compute_metrics(self):
        log_domain = self._log_domain()
        msg_domain = self._message_domain()

        log_model = self.env["mail.gateway.webhook.log"].sudo()
        msg_model = self.env["mail.message"].sudo()
        reaction_model = self.env["mail.message.reaction"].sudo()

        total_logs = log_model.search_count(log_domain)
        inbound_logs = log_model.search_count(log_domain + [("direction", "=", "in")])
        outbound_logs = log_model.search_count(log_domain + [("direction", "=", "out")])
        processed_logs = log_model.search_count(log_domain + [("status", "=", "processed")])
        error_logs = log_model.search_count(
            log_domain + ["|", ("status", "=", "error"), ("http_status", ">=", 400)]
        )
        http_status_values = log_model.search(log_domain).mapped("http_status")
        http_status_values = [val for val in http_status_values if val]
        avg_http_status = (
            sum(http_status_values) / len(http_status_values) if http_status_values else 0
        )

        messages_total = msg_model.search_count(msg_domain)
        messages_with_remote = msg_model.search_count(
            msg_domain + [("gateway_remote_id", "!=", False)]
        )
        reactions_total = reaction_model.search_count([])
        if self.gateway_id:
            reactions_total = reaction_model.search_count(
                [("message_id.gateway_id", "=", self.gateway_id.id)]
            )

        metrics = [
            {"metric_key": "total_logs", "metric_name": "Total Logs", "metric_value": total_logs},
            {"metric_key": "inbound_logs", "metric_name": "Inbound Logs", "metric_value": inbound_logs},
            {"metric_key": "outbound_logs", "metric_name": "Outbound Logs", "metric_value": outbound_logs},
            {"metric_key": "processed_logs", "metric_name": "Processed Logs", "metric_value": processed_logs},
            {"metric_key": "error_logs", "metric_name": "Error Logs", "metric_value": error_logs},
            {
                "metric_key": "avg_http_status",
                "metric_name": "Average HTTP Status",
                "metric_value": round(avg_http_status, 2),
            },
            {"metric_key": "messages_total", "metric_name": "Messages", "metric_value": messages_total},
            {
                "metric_key": "messages_with_remote",
                "metric_name": "Messages w/ Remote ID",
                "metric_value": messages_with_remote,
            },
            {
                "metric_key": "reactions_total",
                "metric_name": "Reactions",
                "metric_value": reactions_total,
            },
        ]
        return metrics

    def _log_domain(self):
        domain = []
        if self.gateway_id:
            domain.append(("gateway_id", "=", self.gateway_id.id))
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("create_date", "<=", self.date_to))
        return domain

    def _message_domain(self):
        domain = []
        if self.gateway_id:
            domain.append(("gateway_id", "=", self.gateway_id.id))
        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.date_to:
            domain.append(("date", "<=", self.date_to))
        return domain

    def _is_enabled(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "mail_discuss_hub_gateway_devtools.metrics_dashboard_enabled",
                default="1",
            )
        )
        return str(param).lower() in ("1", "true", "yes")


class MetricsDashboardLine(models.TransientModel):
    _name = "mail_discuss_hub_dev.metrics_dashboard_line"
    _description = "Metrics Dashboard Line (dev tool)"

    wizard_id = fields.Many2one(
        "mail_discuss_hub_dev.metrics_dashboard_wizard",
        required=True,
        ondelete="cascade",
    )
    metric_key = fields.Char(string="Key")
    metric_name = fields.Char(string="Metric")
    metric_value = fields.Float(string="Value")
