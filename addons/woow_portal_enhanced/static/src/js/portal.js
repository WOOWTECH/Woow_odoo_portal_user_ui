/** @odoo-module **/

/**
 * Woow Portal Enhanced — Frontend JS
 *
 * Handles:
 *  - Module search filter (client-side) on portal home
 *  - Notification page: swipe to mark-as-read / done
 *  - Notification detail modal (click card → fetch detail → show modal)
 *  - MDI icon replacement on portal home module cards
 */

import { whenReady } from "@odoo/owl";

whenReady(() => {
    initSearchFilter();
    initNotificationPage();
    initNotificationModal();
    initReadToggleButtons();
    initMarkAllRead();
    replaceMdiIcons();
});

// ------------------------------------------------------------------
// ① Search filter — client-side module name filtering
// ------------------------------------------------------------------

function initSearchFilter() {
    const input = document.getElementById("wpe_module_search");
    if (!input) return;

    input.addEventListener("keyup", function () {
        const query = this.value.trim().toLowerCase();

        // --- Filter module cards ---
        const cards = document.querySelectorAll(
            "#wpe_module_grid .o_portal_index_card"
        );
        cards.forEach(function (card) {
            const text = card.textContent.toLowerCase();
            if (!query || text.indexOf(query) !== -1) {
                card.classList.remove("wpe-hidden");
            } else {
                card.classList.add("wpe-hidden");
            }
        });

        // Hide/show empty categories
        const categories = document.querySelectorAll(
            "#wpe_module_grid .o_portal_category"
        );
        categories.forEach(function (cat) {
            const visibleCards = cat.querySelectorAll(
                ".o_portal_index_card:not(.wpe-hidden)"
            );
            if (visibleCards.length === 0 && query) {
                cat.classList.add("wpe-hidden");
            } else {
                cat.classList.remove("wpe-hidden");
            }
        });

        // --- Filter notification preview items ---
        var notifItems = document.querySelectorAll(
            ".wpe-notification-preview .wpe-notification-item"
        );
        notifItems.forEach(function (item) {
            var text = item.textContent.toLowerCase();
            if (!query || text.indexOf(query) !== -1) {
                item.classList.remove("wpe-hidden");
            } else {
                item.classList.add("wpe-hidden");
            }
        });

        // Hide group headers if all items in that group are hidden
        var groupHeaders = document.querySelectorAll(
            ".wpe-notification-preview .wpe-preview-group-header"
        );
        groupHeaders.forEach(function (header) {
            // Collect sibling notification items until next group header
            var items = [];
            var sibling = header.nextElementSibling;
            while (sibling && !sibling.classList.contains("wpe-preview-group-header")) {
                if (sibling.classList.contains("wpe-notification-item")) {
                    items.push(sibling);
                }
                sibling = sibling.nextElementSibling;
            }
            var visibleItems = items.filter(function (it) {
                return !it.classList.contains("wpe-hidden");
            });
            if (visibleItems.length === 0 && query) {
                header.classList.add("wpe-hidden");
            } else {
                header.classList.remove("wpe-hidden");
            }
        });
    });
}

// ------------------------------------------------------------------
// ② Notification Page — swipe + click
// ------------------------------------------------------------------

const SWIPE_THRESHOLD = 100;
const SWIPE_MAX = 200;

function initNotificationPage() {
    const list = document.getElementById("wpe_notif_list");
    if (!list) return;

    const wrappers = list.querySelectorAll(".wpe-notif-card-wrapper");
    wrappers.forEach(function (wrapper) {
        setupSwipe(wrapper);
        setupCardClick(wrapper);
    });

    // Hide hint after first swipe
    let hintHidden = false;
    list.addEventListener("touchstart", function () {
        if (!hintHidden) {
            const hint = document.getElementById("wpe_swipe_hint");
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
    const card = wrapper.querySelector(".wpe-notif-card");
    if (!card) return;

    let didSwipe = false;

    card.addEventListener("touchstart", function () {
        didSwipe = false;
    }, { passive: true });

    card.addEventListener("touchmove", function () {
        didSwipe = true;
    }, { passive: true });

    card.addEventListener("click", function () {
        // Don't open modal if user was swiping or card is being removed
        if (didSwipe || wrapper.classList.contains("wpe-removing")) return;

        const itemType = wrapper.getAttribute("data-item-type");
        const params = {};
        if (itemType === "activity") {
            params.activity_id = wrapper.getAttribute("data-activity-id");
        } else {
            params.notification_id = wrapper.getAttribute("data-notif-id");
        }
        openDetailModal(params, wrapper);
    });
}

function setupSwipe(wrapper) {
    const card = wrapper.querySelector(".wpe-notif-card");
    if (!card) return;

    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let swiping = false;
    let locked = false;

    card.addEventListener("touchstart", function (e) {
        if (wrapper.classList.contains("wpe-removing")) return;
        const touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        currentX = 0;
        swiping = true;
        locked = false;
        card.style.transition = "none";
    }, { passive: true });

    card.addEventListener("touchmove", function (e) {
        if (!swiping) return;
        const touch = e.touches[0];
        let diffX = touch.clientX - startX;
        const diffY = touch.clientY - startY;

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

        const progress = Math.min(currentX / SWIPE_THRESHOLD, 1);
        const bg = wrapper.querySelector(".wpe-notif-swipe-bg");
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
            const diffX = Math.max(0, ev.clientX - startX);
            currentX = Math.min(diffX, SWIPE_MAX);
            card.style.transform = "translateX(" + currentX + "px)";
            const progress = Math.min(currentX / SWIPE_THRESHOLD, 1);
            const bg = wrapper.querySelector(".wpe-notif-swipe-bg");
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
    const card = wrapper.querySelector(".wpe-notif-card");
    if (card) {
        card.style.transition = "transform 0.2s ease";
        card.style.transform = "translateX(0)";
    }
    const bg = wrapper.querySelector(".wpe-notif-swipe-bg");
    if (bg) {
        bg.style.transition = "opacity 0.2s ease";
        bg.style.opacity = "0";
    }
}

function handleSwipeAction(wrapper) {
    const itemType = wrapper.getAttribute("data-item-type");
    wrapper.classList.add("wpe-removing");

    const card = wrapper.querySelector(".wpe-notif-card");
    if (card) {
        card.style.transition = "transform 0.3s ease";
        card.style.transform = "translateX(110%)";
    }

    if (itemType === "activity") {
        // Activity: mark as done (deletes the record)
        const activityId = wrapper.getAttribute("data-activity-id");
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
        const notifId = wrapper.getAttribute("data-notif-id");
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

            const currentTab = getCurrentTab();
            if (currentTab === "all") {
                // Stay in list, just update visuals
                wrapper.classList.remove("wpe-removing", "wpe-notif-unread");
                wrapper.classList.add("wpe-notif-read");
                if (card) {
                    card.style.transition = "transform 0.2s ease";
                    card.style.transform = "translateX(0)";
                }
                const dot = wrapper.querySelector(".wpe-unread-dot");
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
    const remaining = document.querySelectorAll(".wpe-notif-card-wrapper");
    if (remaining.length === 0) {
        const list = document.getElementById("wpe_notif_list");
        if (list) {
            list.innerHTML =
                '<div class="wpe-notif-empty text-center text-muted py-5">' +
                '<i class="fa fa-check-circle fa-3x mb-3 d-block" style="opacity: 0.3;"></i>' +
                '<p class="mb-0">沒有通知</p></div>';
        }
    }
}

function getCurrentTab() {
    const activeTab = document.querySelector(".wpe-notif-tab.active");
    if (!activeTab) return "all";
    const href = activeTab.getAttribute("href") || "";
    if (href.indexOf("tab=message") !== -1) return "message";
    if (href.indexOf("tab=notification") !== -1) return "notification";
    if (href.indexOf("tab=activity") !== -1) return "activity";
    return "all";
}

function updateBadgeCounts(unreadCount) {
    const badges = document.querySelectorAll("[data-unread-badge]");
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
// ②-B Read toggle button (per notification)
// ------------------------------------------------------------------

function initReadToggleButtons() {
    var btns = document.querySelectorAll(".wpe-read-toggle-btn");
    btns.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.stopPropagation(); // Don't open the detail modal
            var notifId = btn.getAttribute("data-notif-id");
            if (!notifId) return;

            var isRead = btn.classList.contains("wpe-is-read");
            var action = isRead ? "mark_unread" : "mark_read";

            btn.style.pointerEvents = "none";
            btn.style.opacity = "0.5";

            jsonRpc("/my/notifications/action", {
                notification_id: notifId,
                action: action,
            }).then(function (data) {
                btn.style.pointerEvents = "";
                btn.style.opacity = "";
                if (!data || !data.success) return;

                var wrapper = btn.closest(".wpe-notif-card-wrapper");
                if (action === "mark_read") {
                    btn.classList.remove("wpe-is-unread");
                    btn.classList.add("wpe-is-read");
                    btn.title = "標記未讀";
                    if (wrapper) {
                        wrapper.classList.remove("wpe-notif-unread");
                        wrapper.classList.add("wpe-notif-read");
                    }
                } else {
                    btn.classList.remove("wpe-is-read");
                    btn.classList.add("wpe-is-unread");
                    btn.title = "標記已讀";
                    if (wrapper) {
                        wrapper.classList.remove("wpe-notif-read");
                        wrapper.classList.add("wpe-notif-unread");
                    }
                }
                updateBadgeCounts(data.unread_count);
                updateMarkAllReadBtn(data.unread_count);
            });
        });
    });
}

// ------------------------------------------------------------------
// ②-C Mark all as read
// ------------------------------------------------------------------

function initMarkAllRead() {
    var btn = document.getElementById("wpe_mark_all_read");
    if (!btn) return;

    btn.addEventListener("click", function () {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>處理中...';

        jsonRpc("/my/notifications/mark_all_read", {}).then(function (data) {
            if (data && data.success) {
                // Update all cards to read state
                var wrappers = document.querySelectorAll(".wpe-notif-card-wrapper.wpe-notif-unread");
                wrappers.forEach(function (w) {
                    w.classList.remove("wpe-notif-unread");
                    w.classList.add("wpe-notif-read");
                    var toggle = w.querySelector(".wpe-read-toggle-btn");
                    if (toggle) {
                        toggle.classList.remove("wpe-is-unread");
                        toggle.classList.add("wpe-is-read");
                        toggle.title = "標記未讀";
                    }
                });
                updateBadgeCounts(0);
                btn.innerHTML = '<i class="fa fa-check me-1"></i>已完成';
                setTimeout(function () { btn.style.display = "none"; }, 1000);
            } else {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa fa-check-double me-1"></i>全部已讀';
            }
        });
    });
}

function updateMarkAllReadBtn(unreadCount) {
    var btn = document.getElementById("wpe_mark_all_read");
    if (!btn) return;
    if (unreadCount <= 0) {
        btn.style.display = "none";
    }
}

// ------------------------------------------------------------------
// ③ Detail Modal
// ------------------------------------------------------------------

function initNotificationModal() {
    const overlay = document.getElementById("wpe_notif_modal_overlay");
    if (!overlay) return;

    // Close on overlay background click
    overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeDetailModal();
    });

    // Close button
    const closeBtn = document.getElementById("wpe_modal_close");
    if (closeBtn) {
        closeBtn.addEventListener("click", closeDetailModal);
    }

    // Escape key
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeDetailModal();
    });
}

function openDetailModal(params, wrapper) {
    const overlay = document.getElementById("wpe_notif_modal_overlay");
    if (!overlay) return;

    // Store reference for action button
    overlay._currentParams = params;
    overlay._currentWrapper = wrapper;

    // Show loading state
    const body = document.getElementById("wpe_modal_body");
    body.innerHTML =
        '<div class="text-center py-4">' +
        '<i class="fa fa-spinner fa-spin fa-2x"></i></div>';

    const title = document.getElementById("wpe_modal_title");
    title.textContent = "載入中...";

    // Hide buttons initially
    const docLink = document.getElementById("wpe_modal_doc_link");
    const actionBtn = document.getElementById("wpe_modal_action_btn");
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
    const title = document.getElementById("wpe_modal_title");
    const body = document.getElementById("wpe_modal_body");
    const docLink = document.getElementById("wpe_modal_doc_link");
    const actionBtn = document.getElementById("wpe_modal_action_btn");
    const overlay = document.getElementById("wpe_notif_modal_overlay");

    const detail = data.detail;

    if (data.type === "notification") {
        renderNotificationDetail(detail, title, body, docLink, actionBtn, overlay);
    } else if (data.type === "activity") {
        renderActivityDetail(detail, title, body, docLink, actionBtn, overlay);
    }
}

function renderNotificationDetail(detail, title, body, docLink, actionBtn, overlay) {
    title.textContent = detail.subject;

    let html = '';

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
        const notifId = overlay._currentParams.notification_id;
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
                const wrapper = overlay._currentWrapper;
                if (wrapper) {
                    wrapper.classList.remove("wpe-notif-unread");
                    wrapper.classList.add("wpe-notif-read");
                    const dot = wrapper.querySelector(".wpe-unread-dot");
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

    let html = '';

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
        const activityId = overlay._currentParams.activity_id;
        if (!activityId) return;
        actionBtn.disabled = true;
        actionBtn.innerHTML =
            '<i class="fa fa-spinner fa-spin me-1"></i>處理中...';

        const action = detail.can_approve ? "approve" : "done";
        jsonRpc("/my/notifications/action", {
            activity_id: activityId,
            action: action,
        }).then(function (result) {
            if (result && result.success) {
                actionBtn.innerHTML =
                    '<i class="fa fa-check me-1"></i>已完成';

                // Remove the card from the list
                const wrapper = overlay._currentWrapper;
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
    const overlay = document.getElementById("wpe_notif_modal_overlay");
    if (overlay) {
        overlay.style.display = "none";
        overlay._currentParams = null;
        overlay._currentWrapper = null;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ------------------------------------------------------------------
// ④ MDI Icon replacement — swap Odoo default icons with MDI SVGs
// ------------------------------------------------------------------

const MDI_ICON_MAP = new Map([
    ["/sale/static/src/img/bag.svg", "/woow_portal_enhanced/static/src/img/mdi/cart-outline.svg"],
    ["/account/static/src/img/Bill.svg", "/woow_portal_enhanced/static/src/img/mdi/receipt-text-outline.svg"],
    ["/web/static/img/folder.svg", "/woow_portal_enhanced/static/src/img/mdi/folder-open-outline.svg"],
    ["/project/static/src/img/tasks.svg", "/woow_portal_enhanced/static/src/img/mdi/checkbox-marked-circle-outline.svg"],
    ["/hr_timesheet/static/img/timesheet.svg", "/woow_portal_enhanced/static/src/img/mdi/clock-outline.svg"],
    ["/web/static/img/rfq.svg", "/woow_portal_enhanced/static/src/img/mdi/file-search-outline.svg"],
    ["/purchase/static/src/img/calculator.svg", "/woow_portal_enhanced/static/src/img/mdi/package-variant-closed.svg"],
    ["/portal/static/src/img/portal-connection.svg", "/woow_portal_enhanced/static/src/img/mdi/shield-lock-outline.svg"],
    // Additional common Odoo 18 modules
    ["/helpdesk/static/src/img/helpdesk.svg", "/woow_portal_enhanced/static/src/img/mdi/headset.svg"],
    ["/sign/static/description/icon.svg", "/woow_portal_enhanced/static/src/img/mdi/draw-pen.svg"],
    ["/documents/static/src/img/documents.svg", "/woow_portal_enhanced/static/src/img/mdi/file-multiple-outline.svg"],
    ["/subscription/static/src/img/subscription.svg", "/woow_portal_enhanced/static/src/img/mdi/autorenew.svg"],
    ["/appointment/static/src/img/appointment.svg", "/woow_portal_enhanced/static/src/img/mdi/calendar-check-outline.svg"],
    ["/fleet/static/src/img/fleet.svg", "/woow_portal_enhanced/static/src/img/mdi/car-outline.svg"],
    ["/maintenance/static/src/img/maintenance.svg", "/woow_portal_enhanced/static/src/img/mdi/wrench-outline.svg"],
    ["/event/static/description/icon.svg", "/woow_portal_enhanced/static/src/img/mdi/calendar-star.svg"],
    ["/website_slides/static/src/img/slides.svg", "/woow_portal_enhanced/static/src/img/mdi/school-outline.svg"],
    ["/survey/static/src/img/survey.svg", "/woow_portal_enhanced/static/src/img/mdi/clipboard-text-outline.svg"],
]);

function replaceMdiIcons() {
    const icons = document.querySelectorAll(".o_portal_my_home .o_portal_icon img");
    icons.forEach(function (img) {
        const src = img.getAttribute("src");
        if (!src) return;

        // Special case: Bill.svg used for both invoices and vendor bills
        if (src === "/account/static/src/img/Bill.svg") {
            const link = img.closest("a");
            const href = link ? link.getAttribute("href") : "";
            if (href && href.indexOf("filterby=bills") !== -1) {
                img.setAttribute("src", "/woow_portal_enhanced/static/src/img/mdi/credit-card-outline.svg");
                return;
            }
        }

        if (MDI_ICON_MAP.has(src)) {
            img.setAttribute("src", MDI_ICON_MAP.get(src));
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
