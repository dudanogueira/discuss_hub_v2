/* @odoo-module */

import { threadActionsRegistry } from "@mail/core/common/thread_actions";
import { _t } from "@web/core/l10n/translation";

threadActionsRegistry
    .add("join-channel", {
        condition(component) {
            const thread = component.thread;
            return (
                thread?.model === "discuss.channel" &&
                thread.channel_type === "gateway" &&
                !thread.selfMember &&
                (!component.props.chatWindow || component.props.chatWindow.isOpen)
            );
        },
        icon: "fa fa-fw fa-sign-in",
        iconLarge: "fa fa-fw fa-lg fa-sign-in",
        name: _t("Join Channel"),
        sequence: 11,
        sequenceGroup: 20,
        async open(component) {
            const thread = component.thread;
            try {
                await component.store.joinChannel(thread.id, thread.name);
            } catch {
                component.env.services.notification.add(_t("Unable to join channel."), {
                    type: "danger",
                });
            }
        },
    })
    .add("transfer-channel", {
        condition(component) {
            const thread = component.thread;
            return (
                thread?.model === "discuss.channel" &&
                thread.channel_type === "gateway" &&
                thread.selfMember &&
                (!component.props.chatWindow || component.props.chatWindow.isOpen)
            );
        },
        icon: "fa fa-fw fa-share-square-o",
        iconLarge: "fa fa-fw fa-lg fa-share-square-o",
        name: _t("Transferir"),
        sequence: 12,
        sequenceGroup: 20,
    })
    .add("leave-channel", {
        condition(component) {
            const thread = component.thread;
            return (
                thread?.model === "discuss.channel" &&
                thread.channel_type === "gateway" &&
                thread.selfMember &&
                (!component.props.chatWindow || component.props.chatWindow.isOpen)
            );
        },
        icon: "fa fa-fw fa-sign-out",
        iconLarge: "fa fa-fw fa-lg fa-sign-out",
        name: _t("Leave Channel"),
        sequence: 13,
        sequenceGroup: 20,
        async open(component) {
            try {
                await component.thread.leave();
            } catch {
                component.env.services.notification.add(_t("Unable to leave channel."), {
                    type: "danger",
                });
            }
        },
    })
    .add("resolve-channel", {
        condition(component) {
            const thread = component.thread;
            return (
                thread?.model === "discuss.channel" &&
                thread.channel_type === "gateway" &&
                thread.selfMember &&
                (!component.props.chatWindow || component.props.chatWindow.isOpen)
            );
        },
        icon: "fa fa-fw fa-check-square-o",
        iconLarge: "fa fa-fw fa-lg fa-check-square-o",
        name: _t("Resolver/Arquivar"),
        sequence: 14,
        sequenceGroup: 20,
        async open(component) {
            const thread = component.thread;
            try {
                await component.env.services.orm.call("discuss.channel", "action_archive", [[thread.id]]);
                if ("active" in thread) {
                    thread.active = false;
                }
            } catch {
                component.env.services.notification.add(_t("Unable to archive channel."), {
                    type: "danger",
                });
            }
        },
    });
