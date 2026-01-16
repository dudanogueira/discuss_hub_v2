# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    webhook_log_enabled = fields.Boolean(
        string="Persist webhook logs",
        config_parameter="mail_discuss_hub_gateway_devtools.webhook_log_enabled",
        default=True,
        help="Store inbound/outbound webhook payloads for debugging.",
    )
    webhook_analysis_enabled = fields.Boolean(
        string="Webhook analysis panel",
        config_parameter="mail_discuss_hub_gateway_devtools.webhook_analysis_enabled",
        default=True,
        help="Enable the raw vs normalized analysis view.",
    )
    payload_inspector_enabled = fields.Boolean(
        string="Payload inspector",
        config_parameter="mail_discuss_hub_gateway_devtools.payload_inspector_enabled",
        default=True,
        help="Enable payload validation and diff tools.",
    )
    controlled_replay_enabled = fields.Boolean(
        string="Controlled replay",
        config_parameter="mail_discuss_hub_gateway_devtools.controlled_replay_enabled",
        default=True,
        help="Enable replay with throttling and overrides.",
    )
    unified_timeline_enabled = fields.Boolean(
        string="Unified timeline",
        config_parameter="mail_discuss_hub_gateway_devtools.unified_timeline_enabled",
        default=True,
        help="Enable timeline views per channel/guest.",
    )
    idempotency_map_enabled = fields.Boolean(
        string="Idempotency map",
        config_parameter="mail_discuss_hub_gateway_devtools.idempotency_map_enabled",
        default=True,
        help="Enable dedupe key diagnostics.",
    )
    error_panel_enabled = fields.Boolean(
        string="Error panel",
        config_parameter="mail_discuss_hub_gateway_devtools.error_panel_enabled",
        default=True,
        help="Enable error aggregation dashboards.",
    )
    connection_simulator_enabled = fields.Boolean(
        string="Connection simulator",
        config_parameter="mail_discuss_hub_gateway_devtools.connection_simulator_enabled",
        default=True,
        help="Enable synthetic event generator.",
    )
    provider_comparator_enabled = fields.Boolean(
        string="Provider comparator",
        config_parameter="mail_discuss_hub_gateway_devtools.provider_comparator_enabled",
        default=True,
        help="Enable provider payload comparison.",
    )
    trace_correlation_enabled = fields.Boolean(
        string="Trace correlation",
        config_parameter="mail_discuss_hub_gateway_devtools.trace_correlation_enabled",
        default=True,
        help="Enable trace ID correlation views.",
    )
    metrics_dashboard_enabled = fields.Boolean(
        string="Metrics dashboard",
        config_parameter="mail_discuss_hub_gateway_devtools.metrics_dashboard_enabled",
        default=True,
        help="Enable dev metrics dashboards.",
    )
    gap_checklist_enabled = fields.Boolean(
        string="Gap checklist",
        config_parameter="mail_discuss_hub_gateway_devtools.gap_checklist_enabled",
        default=True,
        help="Enable missing-event checklist.",
    )
