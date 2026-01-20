import { Message } from "@mail/core/common/message_model";
import { patch } from "@web/core/utils/patch";

const WHATSAPP_GATEWAY_TYPES = new Set([
    "whatsapp",
    "whatsapp_evolution_api",
    "whatsapp_waha",
]);

patch(Message.prototype, {
    get gatewayStatusIcon() {
        if (!WHATSAPP_GATEWAY_TYPES.has(this.gateway_type)) {
            return null;
        }
        if (!this.gateway_from_me) {
            return null;
        }
        switch (this.gateway_message_status) {
            case "pending":
                return "fa fa-clock-o";
            case "sent":
                return "fa fa-check";
            case "delivered":
                return "fa fa-check o-whatsapp-check-double";
            case "read":
                return "fa fa-check text-info o-whatsapp-check-double";
            case "failed":
                return "fa fa-exclamation text-danger";
            default:
                return null;
        }
    },
    get gatewayStatusTitle() {
        if (!this.gateway_from_me) {
            return "";
        }
        switch (this.gateway_message_status) {
            case "pending":
                return "Pending";
            case "sent":
                return "Sent";
            case "delivered":
                return "Delivered";
            case "read":
                return "Read";
            case "failed":
                return "Failed";
            default:
                return "";
        }
    },
});
