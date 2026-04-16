import { DiscussClientAction } from "@mail/core/public_web/discuss_client_action";
import "@mail/discuss/core/public/discuss_client_action_patch";
import { patch } from "@web/core/utils/patch";

patch(DiscussClientAction.prototype, {
    async restoreDiscussThread() {
        await super.restoreDiscussThread(...arguments);
        if (!this.store.discuss.thread) {
            return;
        }

        const params = new URLSearchParams(window.location.search);
        const isPortalDiscussions = params.has("discussions");

        if (isPortalDiscussions) {
            this.publicState.welcome = false;
            this.store.discuss.thread.defaultDisplayMode = '';
        }

        if (
            this.store.shouldDisplayWelcomeView ||
            this.store.discuss.thread.defaultDisplayMode !== "video_full_screen"
        ) {
            return;
        }

        await this.store.channels.fetch();
    },
});
