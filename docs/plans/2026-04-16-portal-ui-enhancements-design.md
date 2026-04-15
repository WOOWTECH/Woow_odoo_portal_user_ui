# Portal UI Enhancements — Design Plan

Date: 2026-04-16

## Overview

7 enhancements to the Woow Portal Enhanced module, covering greeting card, notification icons, module card styling, breadcrumb navigation, logo behavior, and empty module hiding.

---

## 1. Greeting Card — Add Clock, Date with Weekday, and Timezone

**Current**: `Good Afternoon, Mitchell Admin` / `2026-04-15`
**Target**: Line 1 = `2026-04-15 (二)`, Line 2 = `14:23 UTC+8`

### Changes

**Controller (`portal.py`):**
- In `_prepare_notification_values()`, replace `today_date` with:
  - `today_date_line1`: `2026-04-15 (二)` — date + Chinese weekday abbreviation
  - `today_date_line2`: `14:23 UTC+8` — time + timezone offset
- Use `datetime.now()` with user's timezone from `request.env.user.tz` (fallback `UTC`)
- Chinese weekday map: `['一','二','三','四','五','六','日']`

**Template (`portal_templates.xml`):**
- Replace `<p t-if="today_date" t-esc="today_date"/>` with two lines:
  ```xml
  <p class="mb-0"><t t-esc="today_date_line1"/></p>
  <p class="mb-0"><t t-esc="today_date_line2"/></p>
  ```

**CSS (`portal.css`):**
- Add clock icon style for line 2 (optional, small `fa-clock-o` before time)

---

## 2. Notification Icons — Match Module Card MDI Icons

**Current**: All notification preview items use generic `fa-bell`, `fa-comment`, `fa-exchange` FontAwesome icons in grey circles.
**Target**: Use the same MDI SVG icons as the module cards, based on `msg.model`.

### Changes

**Controller (`portal.py`):**
- Add a `MODEL_ICON_MAP` dict mapping Odoo model names to MDI SVG paths:
  ```python
  MODEL_ICON_MAP = {
      'sale.order': '/woow_portal_enhanced/static/src/img/mdi/cart-outline.svg',
      'account.move': '/woow_portal_enhanced/static/src/img/mdi/receipt-text-outline.svg',
      'project.project': '/woow_portal_enhanced/static/src/img/mdi/folder-open-outline.svg',
      'project.task': '/woow_portal_enhanced/static/src/img/mdi/checkbox-marked-circle-outline.svg',
      'purchase.order': '/woow_portal_enhanced/static/src/img/mdi/package-variant-closed.svg',
      'helpdesk.ticket': '/woow_portal_enhanced/static/src/img/mdi/headset.svg',
      ...
  }
  ```
- In `_notif_to_dict()` and `_activity_to_dict()`, add `icon_img` field:
  - If `msg.model` is in `MODEL_ICON_MAP`, set `icon_img` = SVG path
  - Otherwise, set `icon_img` = `/woow_portal_enhanced/static/src/img/mdi/bell-outline.svg` (fallback)
- Need to add a `bell-outline.svg` MDI icon file

**Template (`portal_templates.xml`):**
- Replace the notification icon rendering from FA icon to MDI img:
  ```xml
  <!-- Old -->
  <div class="wpe-notification-icon me-3">
      <i t-attf-class="fa #{notif['icon']} fa-lg"/>
  </div>
  <!-- New -->
  <div class="wpe-notification-icon me-3">
      <img t-att-src="notif.get('icon_img', '/woow_portal_enhanced/static/src/img/mdi/bell-outline.svg')"
           width="22" height="22" alt=""/>
  </div>
  ```
- Apply same change for all 3 notification groups (留言, 通知, 待辦)

**CSS (`portal.css`):**
- Adjust `.wpe-notification-icon` to use `filter` for theme coloring if needed, or keep icon natural color on grey circle

---

## 3. Module Card Icon Color — Theme Color

**Current**: MDI SVG icons appear black/dark on light grey circle
**Target**: Icons colored with portal theme color (`--o-brand-primary`, default `#714B67`)

### Changes

**CSS (`portal.css`):**
- Add CSS filter or use `fill` via `currentColor`:
  ```css
  .o_portal_my_home .o_portal_icon img {
      filter: none; /* remove any existing filter */
  }
  .o_portal_my_home .o_portal_icon {
      color: var(--o-brand-primary, #714B67);
  }
  ```
- Since MDI SVGs use `fill="currentColor"`, setting `color` on parent should work.
- If SVGs use hardcoded fill, need to add CSS filter approach or modify SVGs to use `currentColor`.

**SVG files**: Check and update all MDI SVG files to use `fill="currentColor"` instead of hardcoded colors.

---

## 4. Breadcrumb — Enlarge by 20%

**Current**: `🏠 / Sales Orders` — small text
**Target**: Entire breadcrumb bar enlarged 20%

### Changes

**CSS (`portal.css`):**
```css
.o_portal .o_portal_navbar {
    font-size: 1.2rem;
}
.o_portal .o_portal_navbar .breadcrumb {
    font-size: 1.2rem;
}
.o_portal .o_portal_navbar .fa-home {
    font-size: 1.3rem;
}
```

---

## 5. Breadcrumb — Add Back Button

**Current**: `🏠 / Sales Orders ... [≡]`
**Target**: `🏠 / Sales Orders ... [← 返回] [≡]`

### Changes

**Template (`portal_templates.xml`):**
- Add a new template inheriting `portal.portal_layout` to inject a back button next to the hamburger (navbar-toggler):
  ```xml
  <template id="portal_breadcrumb_back_btn" inherit_id="portal.portal_layout">
      <xpath expr="//button[hasclass('navbar-toggler')]" position="before">
          <a href="/my/home" class="btn btn-sm btn-outline-secondary wpe-breadcrumb-back-btn">
              <i class="fa fa-arrow-left me-1"/>返回
          </a>
      </xpath>
  </template>
  ```
- The back button uses `history.back()` via JS, with fallback to `/my/home`

**JS (`portal.js`):**
- Add click handler for `.wpe-breadcrumb-back-btn`:
  ```javascript
  document.querySelector('.wpe-breadcrumb-back-btn')?.addEventListener('click', function(e) {
      e.preventDefault();
      if (window.history.length > 1) {
          window.history.back();
      } else {
          window.location.href = '/my/home';
      }
  });
  ```

**CSS (`portal.css`):**
- Style to match the notification page's `← 返回` button

---

## 6. Logo Link — Always Go to Portal Home

**Current**: Logo `<a href="/">` → backend users go to Odoo backend
**Target**: Logo always links to `/my/home`

### Changes

**Template (`portal_templates.xml`):**
- Override the navbar logo link in `portal.frontend_layout`:
  ```xml
  <template id="portal_logo_to_home" inherit_id="portal.frontend_layout">
      <xpath expr="//a[hasclass('navbar-brand')]" position="attributes">
          <attribute name="href">/my/home</attribute>
      </xpath>
  </template>
  ```

---

## 7. Hide Empty Module Cards

**Current**: All module cards show on home page, even with 0 records (e.g., "Requests for Quotation" shows but has no data)
**Target**: Only show module cards when user has >= 1 record

### Analysis

Odoo already has this mechanism built-in:
- Cards use `placeholder_count` → start hidden (`d-none`)
- JS calls `/my/counters` → reveals cards with count > 0
- `config_card=True` cards (Connection & Security) always show

The issue in the screenshot is likely because Mitchell Admin (backend user) has admin access, so `rfq_count` returns records visible to admin but the portal listing applies different domain filters.

### Changes

**JS (`portal.js`):**
- After the counter update completes, add a secondary check:
  - For cards where count == 0, ensure they stay hidden
  - For `config_card` cards (Connection & Security), always keep visible
- Override `_getCountersAlwaysDisplayed()` if needed

**Alternative approach** — If the issue is that some cards don't use `placeholder_count` (like alert-style cards with `show_count=True`), add CSS:
```css
/* Hide alert cards (Invoices to pay, Quotations to review) when count is 0 */
```
These cards render with the count directly in the template. If count is 0, Odoo may still render the card. Need to check if the count variable is available at template render time.

**Server-side approach** — In `home()` controller, compute a `hidden_modules` set based on actual record counts for the current user, pass it to the template, and add `d-none` class to cards that should be hidden.

---

## Implementation Order

1. **Task 1**: Greeting card (clock + timezone) — controller + template
2. **Task 2**: Notification icons (model-based MDI) — controller + template
3. **Task 3**: Module card icon color (theme color) — CSS + SVG fixes
4. **Task 4**: Breadcrumb enlarge 20% — CSS only
5. **Task 5**: Breadcrumb back button — template + JS + CSS
6. **Task 6**: Logo link to /my/home — template override
7. **Task 7**: Hide empty module cards — JS enhancement

Deploy and test after each task.

---

## Files Modified

| File | Tasks |
|------|-------|
| `controllers/portal.py` | 1, 2 |
| `views/portal_templates.xml` | 1, 2, 5, 6 |
| `static/src/css/portal.css` | 1, 3, 4, 5 |
| `static/src/js/portal.js` | 5, 7 |
| `static/src/img/mdi/bell-outline.svg` | 2 (new file) |
| `static/src/img/mdi/*.svg` | 3 (update fill to currentColor) |
