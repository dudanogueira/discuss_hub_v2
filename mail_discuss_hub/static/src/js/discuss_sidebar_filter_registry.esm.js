import { DiscussAppCategory } from "@mail/core/public_web/discuss_app_category_model";
import { DiscussSidebarCategories } from "@mail/discuss/core/public_web/discuss_sidebar_categories";
import { cleanTerm } from "@mail/utils/common/format";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";

const discussHubSidebarFilterRegistry = registry.category("discuss_hub.sidebar_filters");

function applyDiscussHubSidebarFilter(threads, activeFilter) {
    if (activeFilter === "all") {
        return threads;
    }
    const providers = discussHubSidebarFilterRegistry.getAll();
    if (!providers.length) {
        return threads;
    }
    const filterKey = activeFilter === "unassigned" ? "isUnassigned" : "isMine";
    return threads.filter((thread) => {
        const matchingProviders = providers.filter(
            (provider) => provider.appliesTo && provider.appliesTo(thread)
        );
        if (!matchingProviders.length) {
            return true;
        }
        return matchingProviders.some((provider) => provider[filterKey]?.(thread));
    });
}

patch(DiscussSidebarCategories.prototype, {
    filteredThreads(threads) {
        const activeFilter = this.store.discuss.discussHubSidebarFilter || "mine";
        if (activeFilter === "mine") {
            const baseThreads = super.filteredThreads(threads);
            return applyDiscussHubSidebarFilter(baseThreads, activeFilter);
        }
        const providers = discussHubSidebarFilterRegistry.getAll();
        const searchTerm = this.state.quickSearchVal
            ? cleanTerm(this.state.quickSearchVal)
            : "";
        const baseThreads = threads.filter((thread) => {
            const isProviderThread = providers.some(
                (provider) => provider.appliesTo && provider.appliesTo(thread)
            );
            if (!thread.displayInSidebar && !isProviderThread) {
                return false;
            }
            if (!thread.parent_channel_id && searchTerm) {
                return cleanTerm(thread.displayName).includes(searchTerm);
            }
            return true;
        });
        return applyDiscussHubSidebarFilter(baseThreads, activeFilter);
    },
});

patch(DiscussAppCategory.prototype, {
    get isVisible() {
        const visible = super.isVisible;
        if (visible) {
            return visible;
        }
        const activeFilter = this.store.discuss.discussHubSidebarFilter || "mine";
        if (activeFilter === "mine") {
            return false;
        }
        const providers = discussHubSidebarFilterRegistry.getAll();
        return this.threads.some((thread) =>
            providers.some((provider) => provider.appliesTo && provider.appliesTo(thread))
        );
    },
});
