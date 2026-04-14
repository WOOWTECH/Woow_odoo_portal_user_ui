/**
 * Woow Portal Enhanced — Frontend JS
 *
 * Handles:
 *  - Module search filter (client-side)
 *  - Notification drawer open/close
 *  - Notification tab switching
 *  - Notification actions (approve/reject via JSON-RPC)
 *  - Bell badge count
 */

(function () {
    "use strict";

    // Wait for DOM ready
    document.addEventListener("DOMContentLoaded", function () {
        initBellBadge();
        initSearchFilter();
        initDrawer();
    });

    // ------------------------------------------------------------------
    // Bell badge — fetch count on page load
    // ------------------------------------------------------------------

    function initBellBadge() {
        var badge = document.getElementById("wpe_bell_badge");
        if (!badge) return;

        jsonRpc("/my/notifications", { tab: "all", limit: 0 }).then(function (data) {
            if (data && data.total > 0) {
                badge.textContent = data.total > 99 ? "99+" : data.total;
                badge.classList.remove("d-none");
            }
        });
    }

    // ------------------------------------------------------------------
    // ① Search filter — client-side module name filtering
    // ------------------------------------------------------------------

    function initSearchFilter() {
        var input = document.getElementById("wpe_module_search");
        if (!input) return;

        input.addEventListener("keyup", function () {
            var query = this.value.trim().toLowerCase();
            var cards = document.querySelectorAll(
                "#wpe_module_grid .o_portal_index_card"
            );

            cards.forEach(function (card) {
                var text = card.textContent.toLowerCase();
                if (!query || text.indexOf(query) !== -1) {
                    card.classList.remove("wpe-hidden");
                } else {
                    card.classList.add("wpe-hidden");
                }
            });
        });
    }

    // ------------------------------------------------------------------
    // ② Notification Drawer
    // ------------------------------------------------------------------

    function initDrawer() {
        var drawer = document.getElementById("wpe_drawer");
        var backdrop = document.getElementById("wpe_drawer_backdrop");
        if (!drawer || !backdrop) return;

        var bellTrigger = document.getElementById("wpe_bell_trigger");
        var viewAllLink = document.getElementById("wpe_open_drawer_link");
        var closeBtn = document.getElementById("wpe_drawer_close");
        var currentTab = "all";

        // Open triggers
        if (bellTrigger) {
            bellTrigger.addEventListener("click", function (e) {
                e.preventDefault();
                openDrawer();
            });
        }

        if (viewAllLink) {
            viewAllLink.addEventListener("click", function (e) {
                e.preventDefault();
                openDrawer();
            });
        }

        // Close triggers
        if (closeBtn) {
            closeBtn.addEventListener("click", closeDrawer);
        }
        backdrop.addEventListener("click", closeDrawer);

        // Tab buttons
        var tabBtns = drawer.querySelectorAll(".wpe-tab-btn");
        tabBtns.forEach(function (btn) {
            btn.addEventListener("click", function () {
                tabBtns.forEach(function (b) {
                    b.classList.remove("active");
                });
                this.classList.add("active");
                currentTab = this.getAttribute("data-tab");
                loadNotifications(currentTab);
            });
        });

        // Escape key
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && drawer.classList.contains("open")) {
                closeDrawer();
            }
        });

        function openDrawer() {
            drawer.classList.add("open");
            backdrop.classList.add("open");
            document.body.style.overflow = "hidden";
            loadNotifications(currentTab);
        }

        function closeDrawer() {
            drawer.classList.remove("open");
            backdrop.classList.remove("open");
            document.body.style.overflow = "";
        }
    }

    // ------------------------------------------------------------------
    // Load notifications into drawer
    // ------------------------------------------------------------------

    function loadNotifications(tab) {
        var body = document.getElementById("wpe_drawer_body");
        if (!body) return;

        body.innerHTML =
            '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';

        jsonRpc("/my/notifications", { tab: tab, limit: 50 }).then(function (data) {
            if (!data || !data.activities || data.activities.length === 0) {
                body.innerHTML =
                    '<div class="wpe-drawer-empty">' +
                    '<i class="fa fa-check-circle"></i>' +
                    "<p>沒有通知</p></div>";
                return;
            }

            var html = "";
            data.activities.forEach(function (act) {
                html += buildNotificationCard(act);
            });
            body.innerHTML = html;

            // Bind action buttons
            body.querySelectorAll("[data-action]").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.preventDefault();
                    var actId = this.getAttribute("data-activity-id");
                    var action = this.getAttribute("data-action");
                    handleNotificationAction(actId, action, this);
                });
            });
        });
    }

    function buildNotificationCard(act) {
        var icon = act.icon || "fa-clock-o";
        var actionsHtml = "";

        if (act.can_approve) {
            actionsHtml =
                '<div class="wpe-drawer-card-actions">' +
                '<button class="btn btn-sm btn-wpe-approve" data-action="approve" data-activity-id="' +
                act.id +
                '"><i class="fa fa-check me-1"></i>核准</button>' +
                '<button class="btn btn-sm btn-wpe-reject" data-action="reject" data-activity-id="' +
                act.id +
                '"><i class="fa fa-times me-1"></i>拒絕</button>' +
                "</div>";
        }

        return (
            '<div class="wpe-drawer-card" data-card-id="' +
            act.id +
            '">' +
            '<div class="wpe-drawer-card-header">' +
            '<div class="wpe-drawer-card-icon"><i class="fa ' +
            icon +
            '"></i></div>' +
            "<div>" +
            '<div class="wpe-drawer-card-title">' +
            escapeHtml(act.summary) +
            "</div>" +
            '<div class="wpe-drawer-card-meta">' +
            escapeHtml(act.res_name) +
            " &middot; " +
            escapeHtml(act.time_ago) +
            "</div>" +
            "</div>" +
            "</div>" +
            actionsHtml +
            "</div>"
        );
    }

    // ------------------------------------------------------------------
    // Notification action (approve / reject)
    // ------------------------------------------------------------------

    function handleNotificationAction(activityId, action, btnEl) {
        var card = btnEl.closest(".wpe-drawer-card");
        if (card) card.style.opacity = "0.5";

        jsonRpc("/my/notifications/action", {
            activity_id: activityId,
            action: action,
        }).then(function (data) {
            if (data && data.success) {
                // Remove card with animation
                if (card) {
                    card.style.transition = "opacity 0.3s, max-height 0.3s";
                    card.style.opacity = "0";
                    card.style.maxHeight = "0";
                    card.style.overflow = "hidden";
                    card.style.marginBottom = "0";
                    card.style.padding = "0";
                    setTimeout(function () {
                        card.remove();
                        // Check if drawer is empty
                        var remaining = document.querySelectorAll(".wpe-drawer-card");
                        if (remaining.length === 0) {
                            var body = document.getElementById("wpe_drawer_body");
                            if (body) {
                                body.innerHTML =
                                    '<div class="wpe-drawer-empty">' +
                                    '<i class="fa fa-check-circle"></i>' +
                                    "<p>沒有通知</p></div>";
                            }
                        }
                    }, 300);
                }

                // Update badge
                updateBadge(data.new_count);
            } else {
                if (card) card.style.opacity = "1";
                alert(data && data.error ? data.error : "操作失敗");
            }
        });
    }

    function updateBadge(count) {
        var badge = document.getElementById("wpe_bell_badge");
        if (!badge) return;

        if (count > 0) {
            badge.textContent = count > 99 ? "99+" : count;
            badge.classList.remove("d-none");
        } else {
            badge.classList.add("d-none");
        }
    }

    // ------------------------------------------------------------------
    // JSON-RPC helper
    // ------------------------------------------------------------------

    function jsonRpc(url, params) {
        return fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params || {},
            }),
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.error) {
                    console.error("JSON-RPC error:", data.error);
                    return null;
                }
                return data.result;
            })
            .catch(function (err) {
                console.error("Fetch error:", err);
                return null;
            });
    }

    // ------------------------------------------------------------------
    // Utility
    // ------------------------------------------------------------------

    function escapeHtml(str) {
        if (!str) return "";
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }
})();
