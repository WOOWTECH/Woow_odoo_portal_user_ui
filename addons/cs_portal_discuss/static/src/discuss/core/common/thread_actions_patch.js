/* @odoo-module */

import { threadActionsRegistry } from "@mail/core/common/thread_actions";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";

patch(threadActionsRegistry.get("invite-people"), {

    condition({ thread }) {
        if (!this.component.user.isInternalUser) {
            return false;
        }
        return super.condition(...arguments);
    },
    setup() {
        super.setup(...arguments);
        this.component.user = user;
    }
});