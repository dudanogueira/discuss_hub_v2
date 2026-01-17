import { messageActionsRegistry } from "@mail/core/common/message_actions";
import { useComponent } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

messageActionsRegistry.add("devtools-message-settings", {
    condition: (component) => component.store.self.isAdmin,
    icon: "fa fa-cog",
    title: _t("Message settings"),
    onClick: (component) => {
        const message = component.props.message;
        if (!message?.id) {
            return;
        }
        component.action.doAction({
            type: "ir.actions.act_window",
            res_model: "mail.message",
            res_id: message.id,
            views: [[false, "form"]],
            target: "current",
        });
    },
    setup: () => {
        const component = useComponent();
        component.action = useService("action");
    },
    sequence: 95,
});
