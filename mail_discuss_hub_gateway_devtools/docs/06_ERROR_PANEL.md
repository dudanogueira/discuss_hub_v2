# Error Panel

Goal
- Centralize exceptions and HTTP errors for webhook processing.

Config flag
- `mail_discuss_hub_gateway_devtools.error_panel_enabled`

Steps
1) Filter webhook logs by gateway, direction, and date range.
2) Flag errors by HTTP status and/or processing error fields.
3) Group by endpoint, event, and error class.
4) Export error report (CSV/JSON).

Outputs
- Error dashboard, drill-down view, and export files.
