# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import fields, models


class EvolutionApiInstance(models.Model):
    _inherit = "evolution.api.instance"

    raw_payload = fields.Text(readonly=True)
    raw_payload_pretty = fields.Text(
        compute="_compute_raw_payload_pretty",
        readonly=True,
    )

    def _compute_raw_payload_pretty(self):
        for record in self:
            raw_payload = record.raw_payload or ""
            if not raw_payload:
                record.raw_payload_pretty = ""
                continue
            try:
                parsed = json.loads(raw_payload)
            except Exception:
                record.raw_payload_pretty = raw_payload
                continue
            record.raw_payload_pretty = json.dumps(
                parsed,
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
