# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # All Discuss settings fields are already defined in mail module.
    # This model exists only to allow the dedicated Discuss settings page
    # to work properly with the 'module' context.

    # Standard Odoo behavior: fields named module_<module_name> will install
    # the module when checked and the settings are saved.
    module_mail_discuss_hub_crm = fields.Boolean(
        string="Integrate with CRM",
        help="Install the Discuss Hub CRM integration (syncs Discuss Teams with CRM Teams).",
    )
    module_mail_discuss_hub_helpdesk_mgmt = fields.Boolean(
        string="Integrate with Helpdesk",
        help="Install the Discuss Hub Helpdesk integration (syncs Discuss Teams with Helpdesk Teams).",
    )
