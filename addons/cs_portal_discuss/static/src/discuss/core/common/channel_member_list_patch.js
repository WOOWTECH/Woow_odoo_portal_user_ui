/* @odoo-module */

import { ChannelMemberList } from "@mail/discuss/core/common/channel_member_list";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";

patch(ChannelMemberList.prototype, {
    setup() {
        super.setup();
        this.user = user;
    },
});
