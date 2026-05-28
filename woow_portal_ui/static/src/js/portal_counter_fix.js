/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

if (publicWidget.registry.PortalHomeCounters) {
    publicWidget.registry.PortalHomeCounters.include({
        async _updateCounters() {
            const needed = [...this.el.querySelectorAll('[data-placeholder_count]')]
                .map(el => el.dataset.placeholder_count);
            if (!needed.length) return;

            const numberRpc = Math.min(Math.ceil(needed.length / 5), 3);
            const counterByRpc = Math.ceil(needed.length / numberRpc);
            const countersAlwaysDisplayed = this._getCountersAlwaysDisplayed();

            const proms = [...Array(Math.min(numberRpc, needed.length)).keys()].map(async (i) => {
                const data = await rpc("/my/counters", {
                    counters: needed.slice(i * counterByRpc, (i + 1) * counterByRpc),
                });
                Object.keys(data).forEach((name) => {
                    const el = this.el.querySelector(`[data-placeholder_count='${name}']`);
                    if (!el) return;  // ← THE FIX: skip missing elements
                    el.textContent = data[name];
                    if (data[name] !== 0 || countersAlwaysDisplayed.includes(name)) {
                        el.closest(".o_portal_index_card")?.classList.remove("d-none");
                    }
                });
                return data;
            });
            return Promise.all(proms).then(() => {
                const spinner = this.el.querySelector(".o_portal_doc_spinner");
                if (spinner) spinner.remove();
            });
        },
    });
}