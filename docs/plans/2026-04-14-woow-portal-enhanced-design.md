# woow_portal_enhanced — Module Design

## 1. Overview

| Field       | Value                                |
|-------------|--------------------------------------|
| Module      | `woow_portal_enhanced`               |
| Version     | 18.0.1.0.0                           |
| Depends     | `portal`, `mail`                     |
| License     | LGPL-3                               |
| Author      | WoowTech                             |
| Target      | Odoo 18.0                            |

**Purpose**: Enhance the Odoo 18 Portal user experience to feel like a native mobile app — for both portal users and backend (admin) users.

**Theme color**: Follows the Odoo backend user-selected theme color (not hardcoded). Brand accent elements reference the Woowtech design system.

## 2. Functional Blocks

### Block ① — Search Bar

- **Position**: Fixed below the header, does not scroll with page content.
- **Behavior**: Client-side JS filter — as the user types, module cards on the page are shown/hidden by matching name text. No API call.
- **UI**: Rounded input with magnifying glass icon, placeholder "搜尋模組..." / "Search modules...".
- **RWD**: Full width on all breakpoints.

### Block ② — Notification Center

**Data source**: `mail.activity` filtered by `user_id = current user`.

**Entry A — Bell icon (Header)**:
- Placed in the portal header, next to the user name.
- Red badge shows the count of pending activities.
- Click opens the Drawer.

**Entry B — Recent Notifications section (Page)**:
- Positioned below the search bar on `/my/home`.
- Shows the 3 most recent activities (icon + title + relative time).
- "View all" link opens the Drawer.

**Drawer (right-slide panel)**:
- Slides in from the right, overlays the page.
- Three tabs: All / To-Do / System.
- Each card: activity type icon, summary, source record name, relative timestamp.
- Action buttons: "Approve" / "Reject" when applicable — calls `mail.activity` `action_feedback` via JSON-RPC.
- Close via X button or clicking the overlay backdrop.

**Data endpoint**: New JSON controller `/my/notifications` returns activity list.

### Block ③ — All Modules (replaces "My Account")

- **Replaces** the original `/my/home` "My Account" section.
- **Layout**: 2-column card grid (≥ 768px), 1-column (< 768px).
- **Each card**: Icon + module name + subtitle (e.g. "打卡、請假") + link.
- **Dynamic rendering**: Uses Odoo's existing `_prepare_home_portal_values` mechanism. Only modules the user has permission to access are displayed.
- **Style**: Cards with subtle border-radius, light shadow, consistent padding. Follows Odoo theme color for active/hover states.

### Block ④ — Backend ↔ Portal Switch (Admin only)

**Backend → Portal (Entry A)**:
- Add "Switch to Portal" item in the Odoo backend user dropdown menu (top-right avatar).
- Click navigates to `/my/home`.

**Portal → Backend (Entry B)**:
- In the portal user dropdown menu, show "Return to Backend" for users with `base.group_user` permission.
- Click navigates to `/odoo`.

**Admin Banner**:
- When a backend user (with `base.group_user`) is browsing Portal pages, display an Odoo default-style info banner at the top.
- Banner text: "You are viewing the portal as an administrator" + "Return to Backend" button.
- Uses Odoo's native `alert` / banner styling — no custom colors.

## 3. Technical Architecture

### 3.1 File Structure

```
woow_portal_enhanced/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── portal.py                # Override portal home + notification endpoint
├── models/
│   ├── __init__.py
│   └── res_users.py             # Extend res.users (if needed for settings)
├── views/
│   ├── portal_templates.xml     # QWeb: home page, search, notifications, modules
│   └── webclient_templates.xml  # Backend user menu: "Switch to Portal"
├── security/
│   └── ir.model.access.csv
├── static/
│   └── src/
│       ├── css/
│       │   └── portal.css       # RWD styles, card layout, drawer
│       ├── js/
│       │   └── portal.js        # Search filter, drawer toggle, notification RPC
│       └── img/                 # SVG icons if needed
├── i18n/
│   ├── woow_portal_enhanced.pot
│   └── zh_TW.po
└── tests/
    └── test_portal.py
```

### 3.2 Backend (Python)

**Controller — `controllers/portal.py`**:
- Inherit `portal.portal` and override `/my/home` route.
- Add JSON endpoint `POST /my/notifications` returning `mail.activity` data.
- Add JSON endpoint `POST /my/notifications/action` for approve/reject feedback.

**Model — `models/res_users.py`**:
- Inherit `res.users` if per-user settings are needed (reserved for future).

### 3.3 Frontend (QWeb + JS + CSS)

**Templates — `views/portal_templates.xml`**:
- Inherit `portal.portal_my_home` to replace the body content.
- Add search bar section.
- Add notification preview section.
- Add 2-column module card grid.
- Add admin banner (conditional on `base.group_user`).
- Add notification drawer (hidden by default).

**Templates — `views/webclient_templates.xml`**:
- Inherit the backend user menu template to add "Switch to Portal" item.

**JavaScript — `static/src/js/portal.js`**:
- Search input: `keyup` listener filters `.o_portal_module_card` by text match.
- Bell icon click: toggles drawer visibility with CSS transition.
- Notification tabs: switches visible content in drawer.
- Approve/Reject buttons: `fetch()` JSON-RPC to `/my/notifications/action`.

**CSS — `static/src/css/portal.css`**:
- Search bar sticky positioning.
- Card grid: `display: grid; grid-template-columns: repeat(2, 1fr)` at ≥ 768px, `1fr` below.
- Drawer: fixed position, right-side slide, `transform: translateX(100%)` → `translateX(0)` transition.
- Badge: red dot with count.
- Follow Odoo CSS custom properties for theme color (`--o-brand-primary`, etc.).

### 3.4 RWD Strategy

| Viewport    | Breakpoint  | Layout                        |
|-------------|-------------|-------------------------------|
| Mobile      | < 768px     | Single column, full-width cards |
| Tablet+     | ≥ 768px     | Two column card grid          |

Use CSS media queries. No additional breakpoints.

## 4. Data Flow

### Notification fetch
```
Browser → POST /my/notifications (JSON-RPC)
       → Controller queries mail.activity (user_id = uid)
       → Returns [{id, summary, res_name, activity_type, date_deadline, can_approve}, ...]
```

### Notification action
```
Browser → POST /my/notifications/action (JSON-RPC, {activity_id, action: "approve"|"reject"})
       → Controller calls activity.action_feedback()
       → Returns {success: true}
       → JS removes card from drawer, decrements badge count
```

### Search
```
User types → JS filters DOM elements → No server call
```

## 5. i18n

All user-facing strings wrapped in QWeb `_t()` / Python `_()`.
Provide `zh_TW.po` for Traditional Chinese translation.

## 6. Design Decisions Log

| Decision | Choice | Reason |
|----------|--------|--------|
| Dependencies | Soft — only `portal`, `mail` | Max portability, modules auto-detected |
| Notification source | `mail.activity` | Native Odoo, supports approve/reject |
| Search scope | Module names only (client-side) | Simple, reliable, no API overhead |
| Quick actions block | Removed | Duplicates the module card grid |
| RWD breakpoints | 2-tier (< 768 / ≥ 768) | Matches design mockups |
| Admin banner | Odoo default style | No custom branding needed |
| Theme color | Odoo user-selected | Respects backend theme settings |
