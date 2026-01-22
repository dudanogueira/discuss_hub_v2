import { Record } from "@mail/core/common/record";
import { Thread } from "@mail/core/common/thread_model";
import { DiscussAppCategory } from "@mail/core/public_web/discuss_app_category_model";
import { DiscussSidebarCategories } from "@mail/discuss/core/public_web/discuss_sidebar_categories";
import { cleanTerm } from "@mail/utils/common/format";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";

const discussHubSidebarFilterRegistry = registry.category("discuss_hub.sidebar_filters");

function isThreadArchived(thread) {
    return thread?.active === false;
}

function applyDiscussHubSidebarFilter(threads, activeFilter) {
    const visibleThreads = threads.filter((thread) => !isThreadArchived(thread));
    if (activeFilter === "all") {
        return visibleThreads;
    }
    const providers = discussHubSidebarFilterRegistry.getAll();
    if (!providers.length) {
        return visibleThreads;
    }
    const filterKey = activeFilter === "unassigned" ? "isUnassigned" : "isMine";
    return visibleThreads.filter((thread) => {
        const matchingProviders = providers.filter(
            (provider) => provider.appliesTo && provider.appliesTo(thread)
        );
        if (!matchingProviders.length) {
            return true;
        }
        return matchingProviders.some((provider) => provider[filterKey]?.(thread));
    });
}

patch(Thread.prototype, {
    setup() {
        super.setup(...arguments);
        if (!("active" in this)) {
            this.active = Record.attr(true);
        }
    },
    _computeDiscussAppCategory() {
        if (this.active === false) {
            return;
        }
        return super._computeDiscussAppCategory(...arguments);
    },
});

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
        if (this.hideWhenEmpty) {
            const hasVisibleThreads = this.threads.some(
                (thread) =>
                    !isThreadArchived(thread) &&
                    (thread.displayToSelf || thread.isLocallyPinned)
            );
            if (!hasVisibleThreads) {
                return false;
            }
        }
        const visible = super.isVisible;
        if (visible) {
            return visible;
        }
        const activeFilter = this.store.discuss.discussHubSidebarFilter || "mine";
        if (activeFilter === "mine") {
            return false;
        }
        const providers = discussHubSidebarFilterRegistry.getAll();
        return this.threads.some(
            (thread) =>
                !isThreadArchived(thread) &&
                providers.some((provider) => provider.appliesTo && provider.appliesTo(thread))
        );
    },
});
