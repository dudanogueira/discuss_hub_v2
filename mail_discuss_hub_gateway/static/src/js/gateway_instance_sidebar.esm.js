import {DiscussAppCategory} from "@mail/core/public_web/discuss_app_category_model";
import {Thread} from "@mail/core/common/thread_model";
import {compareDatetime} from "@mail/utils/common/misc";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

const GATEWAY_CATEGORY_PREFIX = "mail_gateway_instance_";
const GATEWAY_CATEGORY_SEQUENCE = 24;

function getGatewayCategory(thread) {
    const gateway = thread.gateway;
    if (!gateway || !gateway.id) {
        return null;
    }
    const store = thread.store;
    if (!store || !store.DiscussAppCategory) {
        return null;
    }
    const categoryId = `${GATEWAY_CATEGORY_PREFIX}${gateway.id}`;
    let category = store.DiscussAppCategory.get({id: categoryId});
    if (!category) {
        category = store.DiscussAppCategory.insert({
            id: categoryId,
            name: gateway.name || _t("Gateway"),
            extraClass: "o-mail-DiscussSidebarCategory-gateway",
            hideWhenEmpty: true,
            canView: false,
            canAdd: true,
            addTitle: _t("Search Gateway Channel"),
            sequence: GATEWAY_CATEGORY_SEQUENCE,
        });
    } else if (gateway.name && category.name !== gateway.name) {
        category.update({name: gateway.name});
    }
    return category;
}

patch(Thread, {
    _insert(data) {
        const thread = super._insert(...arguments);
        if (thread.channel_type === "gateway") {
            const category = getGatewayCategory(thread);
            if (category) {
                const globalCategory = thread.store?.discuss?.gateway;
                if (globalCategory) {
                    globalCategory.threads.delete(thread);
                }
                category.threads.add(thread);
            }
        }
        return thread;
    },
});

patch(Thread.prototype, {
    _computeDiscussAppCategory() {
        if (this.channel_type === "gateway") {
            return getGatewayCategory(this) || super._computeDiscussAppCategory(...arguments);
        }
        return super._computeDiscussAppCategory(...arguments);
    },
});

patch(DiscussAppCategory.prototype, {
    get isVisible() {
        if (this.id === "gateway") {
            return this.threads.some((thread) => thread.displayToSelf || thread.isLocallyPinned);
        }
        return super.isVisible;
    },
    sortThreads(t1, t2) {
        const categoryId = this.id;
        if (
            categoryId === "gateway" ||
            (typeof categoryId === "string" && categoryId.startsWith(GATEWAY_CATEGORY_PREFIX))
        ) {
            return compareDatetime(t2.lastInterestDt, t1.lastInterestDt) || t2.id - t1.id;
        }
        return super.sortThreads(t1, t2);
    },
});
