import { Notification } from "@mail/core/common/notification_model";
import { Record } from "@mail/core/common/record";
import { patch } from "@web/core/utils/patch";

const WHATSAPP_GATEWAY_TYPES = new Set([
    "whatsapp",
    "whatsapp_evolution_api",
    "whatsapp_waha",
]);

patch(Notification.prototype, {
    setup() {
        super.setup();
        this.is_read = Record.attr(false);
    },
    get icon() {
        if (
            this.notification_type === "gateway" &&
            WHATSAPP_GATEWAY_TYPES.has(this.gateway_type)
        ) {
            const statusIcon = this.statusIcon;
            if (statusIcon) {
                return statusIcon;
            }
        }
        return super.icon;
    },
    get statusIcon() {
        if (
            this.notification_type === "gateway" &&
            WHATSAPP_GATEWAY_TYPES.has(this.gateway_type)
        ) {
            if (this.is_read) {
                return "fa fa-check text-info o-whatsapp-check-double";
            }
            switch (this.notification_status) {
                case "pending":
                case "process":
                case "ready":
                    return "fa fa-clock-o";
                case "sent":
                    return "fa fa-check o-whatsapp-check-double";
                case "bounce":
                case "exception":
                    return "fa fa-exclamation text-danger";
                case "canceled":
                    return "fa fa-trash-o text-muted";
            }
        }
        return super.statusIcon;
    },
});
