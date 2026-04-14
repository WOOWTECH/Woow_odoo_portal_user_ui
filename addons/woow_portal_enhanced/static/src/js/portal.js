/**
 * Woow Portal Enhanced — Frontend JS
 *
 * Handles:
 *  - Module search filter (client-side) on portal home
 *  - Notification page: swipe-to-dismiss (mark as done)
 */

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        initSearchFilter();
        initNotificationPage();
    });

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

            // Also hide/show empty categories
            var categories = document.querySelectorAll(
                "#wpe_module_grid .o_portal_category"
            );
            categories.forEach(function (cat) {
                var visibleCards = cat.querySelectorAll(
                    ".o_portal_index_card:not(.wpe-hidden)"
                );
                if (visibleCards.length === 0 && query) {
                    cat.classList.add("wpe-hidden");
                } else {
                    cat.classList.remove("wpe-hidden");
                }
            });
        });
    }

    // ------------------------------------------------------------------
    // ② Notification Page — swipe to dismiss
    // ------------------------------------------------------------------

    var SWIPE_THRESHOLD = 100; // px to trigger action
    var SWIPE_MAX = 200;       // max visual translation

    function initNotificationPage() {
        var list = document.getElementById("wpe_notif_list");
        if (!list) return;

        var wrappers = list.querySelectorAll(".wpe-notif-card-wrapper");
        wrappers.forEach(function (wrapper) {
            setupSwipe(wrapper);
        });

        // Hide hint after first swipe
        var hintHidden = false;
        list.addEventListener("touchstart", function () {
            if (!hintHidden) {
                var hint = document.getElementById("wpe_swipe_hint");
                if (hint) {
                    hint.style.transition = "opacity 0.3s";
                    hint.style.opacity = "0";
                    setTimeout(function () { hint.remove(); }, 300);
                }
                hintHidden = true;
            }
        }, { once: true });
    }

    function setupSwipe(wrapper) {
        var card = wrapper.querySelector(".wpe-notif-card");
        if (!card) return;

        var startX = 0;
        var startY = 0;
        var currentX = 0;
        var swiping = false;
        var locked = false; // prevent vertical scroll conflict

        card.addEventListener("touchstart", function (e) {
            if (wrapper.classList.contains("wpe-removing")) return;
            var touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            currentX = 0;
            swiping = true;
            locked = false;
            card.style.transition = "none";
        }, { passive: true });

        card.addEventListener("touchmove", function (e) {
            if (!swiping) return;
            var touch = e.touches[0];
            var diffX = touch.clientX - startX;
            var diffY = touch.clientY - startY;

            // Lock direction on first significant movement
            if (!locked) {
                if (Math.abs(diffX) > 10 || Math.abs(diffY) > 10) {
                    if (Math.abs(diffY) > Math.abs(diffX)) {
                        // Vertical scroll — abort swipe
                        swiping = false;
                        card.style.transform = "";
                        return;
                    }
                    locked = true;
                }
            }

            // Only allow right swipe
            if (diffX < 0) diffX = 0;
            currentX = Math.min(diffX, SWIPE_MAX);
            card.style.transform = "translateX(" + currentX + "px)";

            // Show/hide swipe bg intensity
            var progress = Math.min(currentX / SWIPE_THRESHOLD, 1);
            var bg = wrapper.querySelector(".wpe-notif-swipe-bg");
            if (bg) {
                bg.style.opacity = progress;
            }

            if (currentX > 10) {
                e.preventDefault();
            }
        }, { passive: false });

        card.addEventListener("touchend", function () {
            if (!swiping) return;
            swiping = false;

            if (currentX >= SWIPE_THRESHOLD) {
                // Trigger "done"
                dismissCard(wrapper);
            } else {
                // Snap back
                card.style.transition = "transform 0.2s ease";
                card.style.transform = "translateX(0)";
                var bg = wrapper.querySelector(".wpe-notif-swipe-bg");
                if (bg) {
                    bg.style.transition = "opacity 0.2s ease";
                    bg.style.opacity = "0";
                }
            }
        });

        // Also support mouse drag for desktop testing
        card.addEventListener("mousedown", function (e) {
            if (wrapper.classList.contains("wpe-removing")) return;
            startX = e.clientX;
            currentX = 0;
            swiping = true;
            card.style.transition = "none";

            function onMouseMove(ev) {
                if (!swiping) return;
                var diffX = Math.max(0, ev.clientX - startX);
                currentX = Math.min(diffX, SWIPE_MAX);
                card.style.transform = "translateX(" + currentX + "px)";
                var progress = Math.min(currentX / SWIPE_THRESHOLD, 1);
                var bg = wrapper.querySelector(".wpe-notif-swipe-bg");
                if (bg) bg.style.opacity = progress;
            }

            function onMouseUp() {
                document.removeEventListener("mousemove", onMouseMove);
                document.removeEventListener("mouseup", onMouseUp);
                if (!swiping) return;
                swiping = false;
                if (currentX >= SWIPE_THRESHOLD) {
                    dismissCard(wrapper);
                } else {
                    card.style.transition = "transform 0.2s ease";
                    card.style.transform = "translateX(0)";
                    var bg = wrapper.querySelector(".wpe-notif-swipe-bg");
                    if (bg) {
                        bg.style.transition = "opacity 0.2s ease";
                        bg.style.opacity = "0";
                    }
                }
            }

            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", onMouseUp);
        });
    }

    function dismissCard(wrapper) {
        var activityId = wrapper.getAttribute("data-activity-id");
        wrapper.classList.add("wpe-removing");

        var card = wrapper.querySelector(".wpe-notif-card");
        if (card) {
            card.style.transition = "transform 0.3s ease";
            card.style.transform = "translateX(110%)";
        }

        // Call API to mark as done
        jsonRpc("/my/notifications/action", {
            activity_id: activityId,
            action: "done",
        }).then(function (data) {
            // Animate collapse
            wrapper.style.transition =
                "max-height 0.3s ease, opacity 0.3s ease, margin 0.3s ease, padding 0.3s ease";
            wrapper.style.maxHeight = "0";
            wrapper.style.opacity = "0";
            wrapper.style.marginBottom = "0";
            wrapper.style.overflow = "hidden";

            setTimeout(function () {
                wrapper.remove();
                // Check empty state
                var remaining = document.querySelectorAll(
                    ".wpe-notif-card-wrapper"
                );
                if (remaining.length === 0) {
                    var list = document.getElementById("wpe_notif_list");
                    if (list) {
                        list.innerHTML =
                            '<div class="wpe-notif-empty text-center text-muted py-5">' +
                            '<i class="fa fa-check-circle fa-3x mb-3 d-block" style="opacity: 0.3;"></i>' +
                            '<p class="mb-0">所有通知已處理完畢</p></div>';
                    }
                }
            }, 300);

            if (!data || !data.success) {
                console.error("Failed to mark activity as done:", data);
            }
        });
    }

    // ------------------------------------------------------------------
    // JSON-RPC helper
    // ------------------------------------------------------------------

    function jsonRpc(url, params) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params || {},
            }),
        })
            .then(function (response) { return response.json(); })
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
})();
