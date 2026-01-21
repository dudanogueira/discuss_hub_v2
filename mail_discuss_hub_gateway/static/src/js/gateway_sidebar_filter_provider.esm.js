import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

const discussHubSidebarFilterRegistry = registry.category("discuss_hub.sidebar_filters");

discussHubSidebarFilterRegistry.add("gateway", {
    appliesTo(thread) {
        return thread.channel_type === "gateway";
    },
    isMine(thread) {
        return Boolean(thread.selfMember);
    },
    isUnassigned(thread) {
        return !thread.channelMembers.some((member) => member.persona?.isInternalUser);
    },
    async fetch({ activeFilter, store, knownChannelIds }) {
        if (activeFilter === "mine") {
            return;
        }
        const data = await rpc("/discuss_hub/channel/fetch", {
            channel_types: ["gateway"],
            known_channel_ids: knownChannelIds,
            limit: 200,
        });
        if (data && Object.keys(data).length) {
            store.insert(data, { html: true });
        }
    },
});
