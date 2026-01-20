/* @odoo-module */

import { threadActionsRegistry } from "@mail/core/common/thread_actions";
import { CrmLeadPanel } from "./crm_lead_panel";
import { _t } from "@web/core/l10n/translation";

threadActionsRegistry.add("crm-lead-panel", {
    condition(component) {
        return (
            component.thread?.model === "discuss.channel" &&
            (!component.props.chatWindow || component.props.chatWindow.isOpen)
        );
    },
    component: CrmLeadPanel,
    componentProps(action, component) {
        return { thread: component.thread };
    },
    icon: "fa fa-fw fa-briefcase",
    iconLarge: "fa fa-fw fa-lg fa-briefcase",
    name: _t("Lead"),
    panelOuterClass: "o-discuss-CrmLeadPanel bg-inherit",
    sequence: 20,
    sequenceGroup: 10,
    toggle: true,
});
