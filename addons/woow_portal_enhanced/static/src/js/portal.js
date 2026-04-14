/**
 * Woow Portal Enhanced — Frontend JS
 *
 * Handles:
 *  - Module search filter (client-side) on portal home
 *  - Notification page: swipe to mark-as-read / done
 *  - Notification detail modal (click card → fetch detail → show modal)
 */

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        initSearchFilter();
        initNotificationPage();
        initNotificationModal();
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
    // ② Notification Page — swipe + click
    // ------------------------------------------------------------------

    var SWIPE_THRESHOLD = 100;
    var SWIPE_MAX = 200;

    function initNotificationPage() {
        var list = document.getElementById("wpe_notif_list");
        if (!list) return;

        var wrappers = list.querySelectorAll(".wpe-notif-card-wrapper");
        wrappers.forEach(function (wrapper) {
            setupSwipe(wrapper);
            setupCardClick(wrapper);
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

    // Click handler — open detail modal
    function setupCardClick(wrapper) {
        var card = wrapper.querySelector(".wpe-notif-card");
        if (!card) return;

        var didSwipe = false;

        card.addEventListener("touchstart", function () {
            didSwipe = false;
        }, { passive: true });

        card.addEventListener("touchmove", function () {
            didSwipe = true;
        }, { passive: true });

        card.addEventListener("click", function (e) {
            // Don't open modal if user was swiping or card is being removed
            if (didSwipe || wrapper.classList.contains("wpe-removing")) return;

            var itemType = wrapper.getAttribute("data-item-type");
            var params = {};
            if (itemType === "activity") {
                params.activity_id = wrapper.getAttribute("data-activity-id");
            } else {
                params.notification_id = wrapper.getAttribute("data-notif-id");
            }
            openDetailModal(params, wrapper);
        });
    }

    function setupSwipe(wrapper) {
        var card = wrapper.querySelector(".wpe-notif-card");
        if (!card) return;

        var startX = 0;
        var startY = 0;
        var currentX = 0;
        var swiping = false;
        var locked = false;

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

            if (!locked) {
                if (Math.abs(diffX) > 10 || Math.abs(diffY) > 10) {
                    if (Math.abs(diffY) > Math.abs(diffX)) {
                        swiping = false;
                        card.style.transform = "";
                        return;
                    }
                    locked = true;
                }
            }

            if (diffX < 0) diffX = 0;
            currentX = Math.min(diffX, SWIPE_MAX);
            card.style.transform = "translateX(" + currentX + "px)";

            var progress = Math.min(currentX / SWIPE_THRESHOLD, 1);
            var bg = wrapper.querySelector(".wpe-notif-swipe-bg");
            if (bg) bg.style.opacity = progress;

            if (currentX > 10) e.preventDefault();
        }, { passive: false });

        card.addEventListener("touchend", function () {
            if (!swiping) return;
            swiping = false;

            if (currentX >= SWIPE_THRESHOLD) {
                handleSwipeAction(wrapper);
            } else {
                snapBack(wrapper);
            }
        });

        // Mouse drag for desktop testing
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
                    handleSwipeAction(wrapper);
                } else {
                    snapBack(wrapper);
                }
            }

            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", onMouseUp);
        });
    }

    function snapBack(wrapper) {
        var card = wrapper.querySelector(".wpe-notif-card");
        if (card) {
            card.style.transition = "transform 0.2s ease";
            card.style.transform = "translateX(0)";
        }
        var bg = wrapper.querySelector(".wpe-notif-swipe-bg");
        if (bg) {
            bg.style.transition = "opacity 0.2s ease";
            bg.style.opacity = "0";
        }
    }

    function handleSwipeAction(wrapper) {
        var itemType = wrapper.getAttribute("data-item-type");
        wrapper.classList.add("wpe-removing");

        var card = wrapper.querySelector(".wpe-notif-card");
        if (card) {
            card.style.transition = "transform 0.3s ease";
            card.style.transform = "translateX(110%)";
        }

        if (itemType === "activity") {
            // Activity: mark as done (deletes the record)
            var activityId = wrapper.getAttribute("data-activity-id");
            jsonRpc("/my/notifications/action", {
                activity_id: activityId,
                action: "done",
            }).then(function (data) {
                collapseAndRemove(wrapper);
                if (!data || !data.success) {
                    console.error("Failed to mark activity as done:", data);
                }
            });
        } else {
            // Notification: mark as read
            var notifId = wrapper.getAttribute("data-notif-id");
            jsonRpc("/my/notifications/action", {
                notification_id: notifId,
                action: "mark_read",
            }).then(function (data) {
                if (!data || !data.success) {
                    console.error("Failed to mark as read:", data);
                    wrapper.classList.remove("wpe-removing");
                    snapBack(wrapper);
                    return;
                }

                var currentTab = getCurrentTab();
                if (currentTab === "all") {
                    // Stay in list, just update visuals
                    wrapper.classList.remove("wpe-removing", "wpe-notif-unread");
                    wrapper.classList.add("wpe-notif-read");
                    if (card) {
                        card.style.transition = "transform 0.2s ease";
                        card.style.transform = "translateX(0)";
                    }
                    var dot = wrapper.querySelector(".wpe-unread-dot");
                    if (dot) dot.remove();
                } else {
                    collapseAndRemove(wrapper);
                }

                updateBadgeCounts(data.unread_count);
            });
        }
    }

    function collapseAndRemove(wrapper) {
        wrapper.style.transition =
            "max-height 0.3s ease, opacity 0.3s ease, margin 0.3s ease, padding 0.3s ease";
        wrapper.style.maxHeight = "0";
        wrapper.style.opacity = "0";
        wrapper.style.marginBottom = "0";
        wrapper.style.overflow = "hidden";

        setTimeout(function () {
            wrapper.remove();
            checkEmptyState();
        }, 300);
    }

    function checkEmptyState() {
        var remaining = document.querySelectorAll(".wpe-notif-card-wrapper");
        if (remaining.length === 0) {
            var list = document.getElementById("wpe_notif_list");
            if (list) {
                list.innerHTML =
                    '<div class="wpe-notif-empty text-center text-muted py-5">' +
                    '<i class="fa fa-check-circle fa-3x mb-3 d-block" style="opacity: 0.3;"></i>' +
                    '<p class="mb-0">沒有通知</p></div>';
            }
        }
    }

    function getCurrentTab() {
        var activeTab = document.querySelector(".wpe-notif-tab.active");
        if (!activeTab) return "all";
        var href = activeTab.getAttribute("href") || "";
        if (href.indexOf("tab=message") !== -1) return "message";
        if (href.indexOf("tab=notification") !== -1) return "notification";
        if (href.indexOf("tab=activity") !== -1) return "activity";
        return "all";
    }

    function updateBadgeCounts(unreadCount) {
        var badges = document.querySelectorAll("[data-unread-badge]");
        badges.forEach(function (b) {
            if (unreadCount > 0) {
                b.textContent = unreadCount;
                b.style.display = "";
            } else {
                b.style.display = "none";
            }
        });
    }

    // ------------------------------------------------------------------
    // ③ Detail Modal
    // ------------------------------------------------------------------

    function initNotificationModal() {
        var overlay = document.getElementById("wpe_notif_modal_overlay");
        if (!overlay) return;

        // Close on overlay background click
        overlay.addEventListener("click", function (e) {
            if (e.target === overlay) closeDetailModal();
        });

        // Close button
        var closeBtn = document.getElementById("wpe_modal_close");
        if (closeBtn) {
            closeBtn.addEventListener("click", closeDetailModal);
        }

        // Escape key
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closeDetailModal();
        });
    }

    function openDetailModal(params, wrapper) {
        var overlay = document.getElementById("wpe_notif_modal_overlay");
        if (!overlay) return;

        // Store reference for action button
        overlay._currentParams = params;
        overlay._currentWrapper = wrapper;

        // Show loading state
        var body = document.getElementById("wpe_modal_body");
        body.innerHTML =
            '<div class="text-center py-4">' +
            '<i class="fa fa-spinner fa-spin fa-2x"></i></div>';

        var title = document.getElementById("wpe_modal_title");
        title.textContent = "載入中...";

        // Hide buttons initially
        var docLink = document.getElementById("wpe_modal_doc_link");
        var actionBtn = document.getElementById("wpe_modal_action_btn");
        docLink.style.display = "none";
        actionBtn.style.display = "none";

        overlay.style.display = "flex";

        jsonRpc("/my/notifications/detail", params).then(function (data) {
            if (!data || !data.success) {
                body.innerHTML = '<p class="text-danger">載入失敗</p>';
                title.textContent = "錯誤";
                return;
            }
            renderModalContent(data);
        });
    }

    function renderModalContent(data) {
        var overlay = document.getElementById("wpe_notif_modal_overlay");
        var title = document.getElementById("wpe_modal_title");
        var body = document.getElementById("wpe_modal_body");
        var docLink = document.getElementById("wpe_modal_doc_link");
        var actionBtn = document.getElementById("wpe_modal_action_btn");

        var detail = data.detail;

        if (data.type === "notification") {
            renderNotificationDetail(detail, title, body, docLink, actionBtn, overlay);
        } else if (data.type === "activity") {
            renderActivityDetail(detail, title, body, docLink, actionBtn, overlay);
        }
    }

    function renderNotificationDetail(detail, title, body, docLink, actionBtn, overlay) {
        title.textContent = detail.subject;

        var html = '';

        // Author and date
        html += '<div class="wpe-modal-meta mb-3">';
        if (detail.author_avatar_url) {
            html += '<img src="' + escapeAttr(detail.author_avatar_url) +
                '" class="wpe-modal-avatar me-2" alt=""/>';
        }
        html += '<span class="fw-semibold">' +
            escapeHtml(detail.author_name) + '</span>';
        html += '<span class="text-muted ms-2">' +
            escapeHtml(detail.date) + '</span>';
        if (detail.subtype_name) {
            html += '<span class="badge bg-light text-dark ms-2">' +
                escapeHtml(detail.subtype_name) + '</span>';
        }
        html += '</div>';

        // Document name
        if (detail.record_name) {
            html += '<div class="mb-3 small text-muted">';
            html += '<i class="fa fa-file-o me-1"></i>';
            html += escapeHtml(detail.record_name);
            html += '</div>';
        }

        // Tracking changes
        if (detail.tracking_details && detail.tracking_details.length > 0) {
            html += '<div class="wpe-modal-tracking mb-3">';
            html += '<h6 class="fw-semibold mb-2">' +
                '<i class="fa fa-exchange me-1"></i>變更記錄</h6>';
            html += '<table class="table table-sm table-bordered">';
            html += '<thead><tr><th>欄位</th><th>原值</th>' +
                '<th>新值</th></tr></thead><tbody>';
            detail.tracking_details.forEach(function (td) {
                html += '<tr><td>' + escapeHtml(td.field_name) +
                    '</td><td>' + escapeHtml(td.old_value) +
                    '</td><td><strong>' + escapeHtml(td.new_value) +
                    '</strong></td></tr>';
            });
            html += '</tbody></table></div>';
        }

        // Message body
        if (detail.body) {
            html += '<div class="wpe-modal-body-content">' +
                detail.body + '</div>';
        }

        body.innerHTML = html;

        // Document link
        if (detail.document_url && detail.document_url !== '#') {
            docLink.href = detail.document_url;
            docLink.style.display = '';
        } else {
            docLink.style.display = 'none';
        }

        // Mark as read button
        actionBtn.style.display = '';
        if (detail.is_read) {
            actionBtn.disabled = true;
            actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>已讀';
        } else {
            actionBtn.disabled = false;
            actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>標記已讀';
        }

        // Wire up action button
        actionBtn.onclick = function () {
            var notifId = overlay._currentParams.notification_id;
            if (!notifId) return;
            actionBtn.disabled = true;
            actionBtn.innerHTML =
                '<i class="fa fa-spinner fa-spin me-1"></i>處理中...';

            jsonRpc("/my/notifications/action", {
                notification_id: notifId,
                action: "mark_read",
            }).then(function (result) {
                if (result && result.success) {
                    actionBtn.innerHTML =
                        '<i class="fa fa-check me-1"></i>已讀';

                    // Update the card in the list
                    var wrapper = overlay._currentWrapper;
                    if (wrapper) {
                        wrapper.classList.remove("wpe-notif-unread");
                        wrapper.classList.add("wpe-notif-read");
                        var dot = wrapper.querySelector(".wpe-unread-dot");
                        if (dot) dot.remove();
                    }
                    updateBadgeCounts(result.unread_count);
                } else {
                    actionBtn.disabled = false;
                    actionBtn.innerHTML =
                        '<i class="fa fa-check me-1"></i>標記已讀';
                }
            });
        };
    }

    function renderActivityDetail(detail, title, body, docLink, actionBtn, overlay) {
        title.textContent = detail.summary;

        var html = '';

        // Activity type badge
        if (detail.activity_type) {
            html += '<div class="mb-3">';
            html += '<span class="badge bg-light text-dark">';
            html += '<i class="fa ' + escapeAttr(detail.icon) +
                ' me-1"></i>';
            html += escapeHtml(detail.activity_type);
            html += '</span>';
            if (detail.date_deadline) {
                html += '<span class="text-muted ms-3">';
                html += '<i class="fa fa-calendar-o me-1"></i>';
                html += escapeHtml(detail.date_deadline);
                html += '</span>';
            }
            html += '</div>';
        }

        // Document name
        if (detail.res_name) {
            html += '<div class="mb-3 small text-muted">';
            html += '<i class="fa fa-file-o me-1"></i>';
            html += escapeHtml(detail.res_name);
            html += '</div>';
        }

        // Note content
        if (detail.note) {
            html += '<div class="wpe-modal-body-content">' +
                detail.note + '</div>';
        } else {
            html += '<div class="text-muted small">沒有詳細說明</div>';
        }

        body.innerHTML = html;

        // Document link
        if (detail.document_url && detail.document_url !== '#') {
            docLink.href = detail.document_url;
            docLink.style.display = '';
        } else {
            docLink.style.display = 'none';
        }

        // Done / Approve button for activity
        actionBtn.style.display = '';
        if (detail.can_approve) {
            actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>核准';
        } else {
            actionBtn.innerHTML = '<i class="fa fa-check me-1"></i>完成';
        }
        actionBtn.disabled = false;

        actionBtn.onclick = function () {
            var activityId = overlay._currentParams.activity_id;
            if (!activityId) return;
            actionBtn.disabled = true;
            actionBtn.innerHTML =
                '<i class="fa fa-spinner fa-spin me-1"></i>處理中...';

            var action = detail.can_approve ? "approve" : "done";
            jsonRpc("/my/notifications/action", {
                activity_id: activityId,
                action: action,
            }).then(function (result) {
                if (result && result.success) {
                    actionBtn.innerHTML =
                        '<i class="fa fa-check me-1"></i>已完成';

                    // Remove the card from the list
                    var wrapper = overlay._currentWrapper;
                    if (wrapper) {
                        collapseAndRemove(wrapper);
                    }

                    // Close modal after a short delay
                    setTimeout(closeDetailModal, 500);
                } else {
                    actionBtn.disabled = false;
                    actionBtn.innerHTML =
                        '<i class="fa fa-check me-1"></i>' +
                        (detail.can_approve ? '核准' : '完成');
                }
            });
        };
    }

    function closeDetailModal() {
        var overlay = document.getElementById("wpe_notif_modal_overlay");
        if (overlay) {
            overlay.style.display = "none";
            overlay._currentParams = null;
            overlay._currentWrapper = null;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeAttr(text) {
        if (!text) return '';
        return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
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
