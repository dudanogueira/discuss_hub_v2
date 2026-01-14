/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ImageField, imageField } from "@web/views/fields/image/image_field";
import { useEffect } from "@odoo/owl";

class EvolutionQrCodeField extends ImageField {
    static template = "mail_gateway_whatsapp_evolution_api_manager.EvolutionQrCodeField";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this._intervalId = null;
        this._polling = false;

        useEffect(
            () => {
                this._resetPolling();
                return () => this._clearPolling();
            },
            () => [this.props.record.resId, this.props.record.data.status]
        );
    }

    get canRefreshQr() {
        return Boolean(this.props.record.resId) && this.props.record.data.status === "connecting";
    }

    _clearPolling() {
        if (this._intervalId) {
            clearInterval(this._intervalId);
            this._intervalId = null;
        }
    }

    _resetPolling() {
        this._clearPolling();
        if (!this.canRefreshQr) {
            return;
        }
        this._pollStatus();
        this._intervalId = setInterval(() => this._pollStatus(), 5000);
    }

    async _pollStatus() {
        if (this._polling || !this.canRefreshQr) {
            return;
        }
        this._polling = true;
        try {
            await this.orm.call("evolution.api.instance", "action_check_status", [
                this.props.record.resId,
            ]);
            await this.props.record.load();
            if (this.props.record.data.status === "connecting") {
                await this.orm.call("evolution.api.instance", "action_refresh_qrcode", [
                    this.props.record.resId,
                ]);
                await this.props.record.load();
            }
        } catch (error) {
            this._clearPolling();
        } finally {
            this._polling = false;
        }
    }

    async onRefreshQr() {
        if (!this.props.record.resId) {
            return;
        }
        await this.orm.call("evolution.api.instance", "action_refresh_qrcode", [
            this.props.record.resId,
        ]);
        await this.props.record.load();
    }
}

registry.category("fields").add("evolution_qr_code", {
    ...imageField,
    component: EvolutionQrCodeField,
});
