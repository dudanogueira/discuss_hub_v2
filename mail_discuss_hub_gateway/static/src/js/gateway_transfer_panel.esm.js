/* @odoo-module */

import { ImStatus } from "@mail/core/common/im_status";
import { ActionPanel } from "@mail/discuss/core/common/action_panel";

import { Component, onMounted, onWillStart, useRef, useState } from "@odoo/owl";

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { useSequential } from "@mail/utils/common/hooks";
import { useDebounced } from "@web/core/utils/timing";

export class GatewayTransferPanel extends Component {
    static components = { ImStatus, ActionPanel };
    static defaultProps = { hasSizeConstraints: false };
    static props = ["hasSizeConstraints?", "thread", "close", "className?"];
    static template = "mail_discuss_hub_gateway.GatewayTransferPanel";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.store = useState(useService("mail.store"));
        this.notification = useService("notification");
        this.suggestionService = useService("mail.suggestion");
        this.inputRef = useRef("input");
        this.sequential = useSequential();
        this.searchStr = "";
        this.state = useState({
            selectablePartners: [],
            selectedPartner: undefined,
            searchResultCount: 0,
            isSubmitting: false,
        });
        this.debouncedFetchPartnersToInvite = useDebounced(this.fetchPartnersToInvite.bind(this), 250);
        onWillStart(() => {
            if (this.store.self.type === "partner") {
                this.fetchPartnersToInvite();
            }
        });
        onMounted(() => {
            if (this.store.self.type === "partner") {
                this.inputRef.el.focus();
            }
        });
    }

    async fetchPartnersToInvite() {
        const results = await this.sequential(() =>
            this.orm.call("res.partner", "search_for_channel_invite", [
                this.searchStr,
                this.props.thread.id,
            ])
        );
        if (!results) {
            return;
        }
        const { Persona: selectablePartners = [] } = this.store.insert(results.data);
        this.state.selectablePartners = this.suggestionService.sortPartnerSuggestions(
            selectablePartners,
            this.searchStr,
            this.props.thread
        );
        this.state.searchResultCount = results.count;
        if (
            this.state.selectedPartner &&
            !this.state.selectablePartners.some((partner) =>
                partner.eq(this.state.selectedPartner)
            )
        ) {
            this.state.selectedPartner = undefined;
        }
    }

    onInput() {
        this.searchStr = this.inputRef.el.value;
        this.debouncedFetchPartnersToInvite();
    }

    onClickSelectablePartner(partner) {
        if (this.state.selectedPartner?.eq(partner)) {
            this.state.selectedPartner = undefined;
            return;
        }
        this.state.selectedPartner = partner;
    }

    onClearSelectedPartner() {
        this.state.selectedPartner = undefined;
    }

    async onClickTransfer() {
        if (!this.state.selectedPartner || this.state.isSubmitting) {
            return;
        }
        this.state.isSubmitting = true;
        try {
            await this.orm.call("discuss.channel", "add_members", [[this.props.thread.id]], {
                partner_ids: [this.state.selectedPartner.id],
            });
            await this.props.thread.leave();
            this.props.close();
            if (this.store.inbox) {
                this.store.inbox.setAsDiscussThread();
            }
        } catch {
            this.notification.add(_t("Unable to transfer channel."), { type: "danger" });
        } finally {
            this.state.isSubmitting = false;
        }
    }
}
