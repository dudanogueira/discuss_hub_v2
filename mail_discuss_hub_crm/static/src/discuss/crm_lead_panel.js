/* @odoo-module */

import { Component, onWillStart, useState } from "@odoo/owl";
import { ActionPanel } from "@mail/discuss/core/common/action_panel";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class CrmLeadPanel extends Component {
    static template = "mail_discuss_hub_crm.CrmLeadPanel";
    static components = { ActionPanel };
    static props = ["thread"];

    setup() {
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.state = useState({
            loading: true,
            creating: false,
            leads: [],
            teams: [],
            name: "",
            teamId: null,
            canCreate: false,
        });
        onWillStart(async () => {
            await this._loadData();
        });
    }

    get hasLeads() {
        return this.state.leads.length > 0;
    }

    async _loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "discuss.channel",
                "action_get_discuss_lead_panel_data",
                [[this.props.thread.id]]
            );
            this.state.leads = data.leads || [];
            this.state.canCreate = !!data.can_create;
            this.state.teamId = data.default_team_id || null;
            if (this.state.canCreate) {
                this.state.teams = await this.orm.searchRead(
                    "crm.team",
                    [],
                    ["id", "name"]
                );
            }
        } catch (error) {
            this.notification.add(_t("Unable to load lead panel data."), {
                type: "danger",
            });
        } finally {
            this.state.loading = false;
        }
    }

    async createLead() {
        const name = this.state.name.trim();
        if (!name) {
            this.notification.add(_t("Lead title is required."), {
                type: "warning",
            });
            return;
        }
        this.state.creating = true;
        try {
            const lead = await this.orm.call(
                "discuss.channel",
                "action_create_discuss_lead",
                [[this.props.thread.id], { name, team_id: this.state.teamId }]
            );
            this.state.leads = [...this.state.leads, lead];
            this.state.name = "";
            this.notification.add(_t("Lead created."), { type: "success" });
        } catch (error) {
            this.notification.add(_t("Unable to create lead."), { type: "danger" });
        } finally {
            this.state.creating = false;
        }
    }

    openLead(leadId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead",
            res_id: leadId,
            views: [[false, "form"]],
        });
    }
}
