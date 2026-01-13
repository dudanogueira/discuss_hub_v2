import { Message } from "@mail/core/common/message";
import { _t } from "@web/core/l10n/translation";
import { markEventHandled } from "@web/core/utils/misc";
import { patch } from "@web/core/utils/patch";

patch(Message.prototype, {
    hasAuthorClickable() {
        if (
            this.message.gateway_type &&
            this.message.author?.type === "guest" &&
            this.message.author.id
        ) {
            return true;
        }
        if (
            this.message.gateway_type &&
            this.message.author?.type === "partner" &&
            this.message.author.id
        ) {
            return true;
        }
        return super.hasAuthorClickable();
    },
    getAuthorText() {
        if (
            this.message.gateway_type &&
            this.message.author?.type === "guest" &&
            this.message.author.id
        ) {
            return _t("Create partner");
        }
        if (
            this.message.gateway_type &&
            this.message.author?.type === "partner" &&
            this.message.author.id &&
            !this.message.author.userId
        ) {
            return _t("Open partner");
        }
        return super.getAuthorText();
    },
    onClickAuthor(ev) {
        if (
            this.message.gateway_type &&
            this.message.author?.type === "guest" &&
            this.message.author.id
        ) {
            ev.stopPropagation();
            return this.env.services.action.doAction({
                name: _t("Manage guest"),
                type: "ir.actions.act_window",
                res_model: "mail.guest.manage",
                context: { default_guest_id: this.message.author.id },
                views: [[false, "form"]],
                target: "new",
            });
        }
        if (
            this.message.gateway_type &&
            this.message.author?.type === "partner" &&
            this.message.author.id &&
            !this.message.author.userId
        ) {
            markEventHandled(ev, "Message.ClickAuthor");
            return this.env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: "res.partner",
                res_id: this.message.author.id,
                views: [[false, "form"]],
                target: "new",
            });
        }
        return super.onClickAuthor(...arguments);
    },
});
