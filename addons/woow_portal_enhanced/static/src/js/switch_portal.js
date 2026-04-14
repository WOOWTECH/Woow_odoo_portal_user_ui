/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";

function switchToPortalItem(env) {
    return {
        type: "item",
        id: "switch_to_portal",
        description: _t("Switch to Portal"),
        callback: () => {
            browser.location.href = "/my/home";
        },
        sequence: 45,
    };
}

registry.category("user_menuitems").add("switch_to_portal", switchToPortalItem);
