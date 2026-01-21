import { discussSidebarItemsRegistry } from "@mail/core/public_web/discuss_sidebar";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { Component, useEffect, useState } from "@odoo/owl";

export class DiscussHubSidebarFilters extends Component {
    static template = "mail_discuss_hub.DiscussHubSidebarFilters";

    setup() {
        this.store = useState(useService("mail.store"));
        this.filterRegistry = registry.category("discuss_hub.sidebar_filters");
        this.loadingFilters = new Set();
        this.labels = {
            mine: _t("Minhas"),
            unassigned: _t("Nao atribuidas"),
            all: _t("Todas"),
        };
        if (!this.store.discuss.discussHubSidebarFilter) {
            this.store.discuss.update({ discussHubSidebarFilter: "mine" });
        }
        useEffect(
            (activeFilter) => {
                this.loadAccessibleThreads(activeFilter);
            },
            () => [this.activeFilter]
        );
    }

    get activeFilter() {
        return this.store.discuss.discussHubSidebarFilter || "mine";
    }

    setFilter(value) {
        this.store.discuss.update({ discussHubSidebarFilter: value });
    }

    async loadAccessibleThreads(activeFilter) {
        if (activeFilter === "mine") {
            return;
        }
        if (this.loadingFilters.has(activeFilter)) {
            return;
        }
        this.loadingFilters.add(activeFilter);
        try {
            const providers = this.filterRegistry.getAll();
            if (!providers.length) {
                return;
            }
            const knownChannelIds = Object.values(this.store.Thread.records)
                .filter((thread) => thread.model === "discuss.channel")
                .map((thread) => thread.id);
            await Promise.all(
                providers.map((provider) =>
                    provider.fetch?.({
                        activeFilter,
                        store: this.store,
                        knownChannelIds,
                        rpc,
                    })
                )
            );
        } finally {
            this.loadingFilters.delete(activeFilter);
        }
    }
}

discussSidebarItemsRegistry.add("discuss_hub_filters", DiscussHubSidebarFilters, { sequence: 25 });
