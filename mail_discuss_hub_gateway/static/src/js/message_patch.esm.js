/* @odoo-module */

import { Message } from "@mail/core/common/message";
import { markEventHandled } from "@web/core/utils/misc";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(Message.prototype, {
    _isGatewayGuestAuthor() {
        return (
            this.message.gateway_type &&
            this.message.author?.type === "guest" &&
            this.message.author.id
        );
    },
    getAuthorText() {
        if (this._isGatewayGuestAuthor()) {
            return _t("Create partner");
        }
        return this.hasAuthorClickable() ? _t("Open card") : undefined;
    },
    onClickAuthor(ev) {
        if (this._isGatewayGuestAuthor()) {
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
        if (this.hasAuthorClickable()) {
            markEventHandled(ev, "Message.ClickAuthor");
            const target = ev.currentTarget;
            if (!this.avatarCard.isOpen) {
                this.avatarCard.open(target, {
                    id: this.message.author.userId,
                });
            }
        }
    },
});
