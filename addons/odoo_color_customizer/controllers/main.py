# -*- coding: utf-8 -*-
"""
Color Customizer - CSS Controller
Serves dynamic CSS with custom primary color variables.
"""
from odoo import http
from odoo.http import request

# Default Odoo Community purple color (from primary_variables.scss: $o-community-color)
DEFAULT_PRIMARY_COLOR = '#71639e'


class ColorCustomizerController(http.Controller):
    """Controller for serving dynamic theme CSS."""

    @http.route('/color_customizer/frontend.css', type='http', auth='public', cors='*')
    def get_frontend_css(self):
        """
        Return CSS for frontend pages including:
        - BUG FIX 34: Editor launcher (triangle + apps button)
        - BUG FIX 40-44: Mobile sidebar and hamburger icon fixes
        """
        # Get configured color or fall back to default
        primary_color = request.env['ir.config_parameter'].sudo().get_param(
            'odoo_color_customizer.primary_color',
            DEFAULT_PRIMARY_COLOR
        )

        # Validate color format
        if not primary_color or not self._is_valid_hex_color(primary_color):
            primary_color = DEFAULT_PRIMARY_COLOR

        # Calculate color variants
        hover_color = self._darken_color(primary_color, 0.1)
        active_color = self._darken_color(primary_color, 0.2)
        light_color = self._lighten_color(primary_color, 0.85)
        text_color = self._get_contrast_color(primary_color)

        # Generate comprehensive frontend CSS
        css = f""":root {{
    --custom-primary: {primary_color};
    --custom-primary-hover: {hover_color};
    --custom-primary-active: {active_color};
    --custom-primary-light: {light_color};
    --custom-primary-text: {text_color};
}}

/* ============================================================================
   BUG FIX 34: Frontend Editor Launcher (Triangle + Apps Button)
   IMPORTANT: Text/icons are ALWAYS WHITE (#ffffff) per user requirement
   Do NOT use {{text_color}} here - user explicitly wants white
   ============================================================================ */
.o_frontend_to_backend_nav::before {{
    border-top-color: {primary_color} !important;
    border-left-color: {primary_color} !important;
}}

.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn {{
    background-color: {primary_color} !important;
    color: #ffffff !important;
}}

.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn:hover {{
    background-color: {hover_color} !important;
    color: #ffffff !important;
}}

/* BUG FIX 40: "所有應用程式" button - the icon is fa-th (FontAwesome grid icon) */
/* The button itself has class "fa fa-th" - it IS the icon, not a container */
.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn.fa,
.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn.fa-th,
.o_frontend_to_backend_nav a.o_frontend_to_backend_apps_btn {{
    color: #ffffff !important;
}}

/* The ::before pseudo-element contains the actual icon glyph */
.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn.fa::before,
.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn.fa-th::before,
.o_frontend_to_backend_nav a.o_frontend_to_backend_apps_btn::before {{
    color: #ffffff !important;
}}

/* BUG FIX 41: Ensure the grid icon (fa-th) is visible */
.o_frontend_to_backend_nav .fa-th,
.o_frontend_to_backend_nav .fa-th::before,
.o_frontend_to_backend_apps_btn.fa-th,
.o_frontend_to_backend_apps_btn.fa-th::before {{
    color: #ffffff !important;
    opacity: 1 !important;
    visibility: visible !important;
}}

/* ============================================================================
   BUG FIX 42: Mobile Hamburger Menu Icon (三條線)
   The .navbar-toggler-icon uses CSS background-image (SVG) not color property
   We need to override the SVG with a white version
   ============================================================================ */

/* Mobile navbar hamburger button - make icon white */
.o_header_mobile .navbar-toggler-icon,
.navbar-toggler-icon {{
    /* Override Bootstrap's default SVG with white-colored SVG */
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='rgba%28255, 255, 255, 1%29' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e") !important;
}}

/* Mobile navbar background - use primary color */
.o_header_mobile,
.o_header_mobile .navbar,
header .navbar.o_header_mobile,
nav.o_header_mobile {{
    background-color: {primary_color} !important;
}}

/* Mobile navbar text should be white */
.o_header_mobile .nav-link,
.o_header_mobile .navbar-brand,
.o_header_mobile a {{
    color: #ffffff !important;
}}

/* Mobile offcanvas menu header */
.o_navbar_mobile .offcanvas-header {{
    background-color: {primary_color} !important;
}}

.o_navbar_mobile .offcanvas-header .btn-close {{
    filter: invert(1) !important;
}}

/* ============================================================================
   BUG FIX 43: Mobile Sidebar "所有應用程式" Button
   The .o_sidebar_topbar contains "所有應用程式" button with cyan background
   Both icon (oi-apps) and text (span.px-2) must be WHITE for contrast
   ============================================================================ */

/* The "所有應用程式" button in mobile sidebar header */
.o_sidebar_topbar a.btn.btn-primary,
.o_sidebar_topbar .btn-primary,
.o_sidebar_topbar a.btn-primary {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: #ffffff !important;
}}

/* Ensure the icon inside the button is white */
.o_sidebar_topbar a.btn.btn-primary .oi,
.o_sidebar_topbar a.btn.btn-primary .oi-apps,
.o_sidebar_topbar a.btn.btn-primary i,
.o_sidebar_topbar .btn-primary .oi,
.o_sidebar_topbar .btn-primary .oi-apps,
.o_sidebar_topbar .btn-primary i {{
    color: #ffffff !important;
}}

/* Ensure the text inside the button is white - 所有應用程式 */
.o_sidebar_topbar a.btn.btn-primary span,
.o_sidebar_topbar a.btn.btn-primary span.px-2,
.o_sidebar_topbar .btn-primary span {{
    color: #ffffff !important;
}}

/* ============================================================================
   BUG FIX 44: Mobile Hamburger Icon (三條線) in Backend Navbar
   The .o_menu_toggle contains fa-bars icon - must be WHITE on cyan navbar
   Currently showing as cyan (same as background) - invisible!
   ============================================================================ */

/* Mobile menu toggle hamburger icon */
.o_menu_toggle,
.o_menu_toggle i,
.o_menu_toggle .fa,
.o_menu_toggle .fa-bars,
a.o_menu_toggle,
a.o_menu_toggle i,
a.o_menu_toggle .fa-bars {{
    color: #ffffff !important;
}}

/* The ::before pseudo-element for FontAwesome icons */
.o_menu_toggle .fa::before,
.o_menu_toggle .fa-bars::before,
a.o_menu_toggle .fa::before,
a.o_menu_toggle .fa-bars::before {{
    color: #ffffff !important;
}}

/* Also ensure mobile navbar has proper colors */
.o_main_navbar .o_menu_toggle,
.o_main_navbar .o_menu_toggle i,
.o_main_navbar .o_menu_toggle .fa-bars,
.o_main_navbar a.o_menu_toggle,
.o_main_navbar a.o_menu_toggle i {{
    color: #ffffff !important;
}}

/* ============================================================================
   PORTAL & PUBLIC USER — Unified Brand Color
   All portal pages, login/signup, and public-facing pages
   ============================================================================ */

/* ---- Portal / Frontend Navbar ---- */
header#top .navbar,
header .navbar,
.o_frontend_header,
nav.navbar.navbar-expand-lg {{
    background-color: {primary_color} !important;
    border-bottom-color: {hover_color} !important;
}}

header#top .navbar .nav-link,
header#top .navbar .navbar-nav .nav-link,
header .navbar .nav-link,
.o_frontend_header .nav-link,
header#top .navbar .navbar-brand,
header .navbar .navbar-brand {{
    color: {text_color} !important;
}}

header#top .navbar .nav-link:hover,
header#top .navbar .nav-link:focus,
header .navbar .nav-link:hover,
header .navbar .nav-link:focus,
.o_frontend_header .nav-link:hover {{
    color: {text_color} !important;
    opacity: 0.85;
}}

/* Navbar dropdown items (user menu, etc.) */
header .navbar .dropdown-menu .dropdown-item:active,
header .navbar .dropdown-menu .dropdown-item.active {{
    background-color: {primary_color} !important;
    color: {text_color} !important;
}}

header .navbar .dropdown-menu .dropdown-item:hover,
header .navbar .dropdown-menu .dropdown-item:focus {{
    background-color: {light_color} !important;
    color: {primary_color} !important;
}}

/* Navbar toggler (hamburger) for portal mobile */
header .navbar .navbar-toggler {{
    border-color: rgba(255,255,255,0.5) !important;
}}

header .navbar .navbar-toggler .navbar-toggler-icon {{
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='rgba%28255, 255, 255, 1%29' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e") !important;
}}

/* eCommerce cart icon in navbar */
header .navbar .badge,
header .navbar .my_cart_quantity {{
    background-color: {hover_color} !important;
    color: {text_color} !important;
}}

/* ---- Portal "My Account" Home Page Icons & Cards ---- */
.o_portal_my_home .o_portal_category .o_portal_category_icon,
.o_portal_my_home .o_portal_index .o_portal_category_icon {{
    color: {primary_color} !important;
}}

.o_portal_my_home .o_portal_category:hover .o_portal_category_icon,
.o_portal_my_home .o_portal_index:hover .o_portal_category_icon {{
    color: {hover_color} !important;
}}

/* Portal doc count badges */
.o_portal_my_home .badge.bg-primary,
.o_portal_my_home .badge.rounded-pill.bg-primary {{
    background-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* ---- Portal Sidebar ---- */
.o_portal_sidebar .nav-link.active,
.o_portal_sidebar .nav-link:hover {{
    color: {primary_color} !important;
}}

.o_portal_sidebar .nav-link.active {{
    border-color: {primary_color} !important;
}}

/* ---- Portal Breadcrumb ---- */
.o_portal .breadcrumb-item a {{
    color: {primary_color} !important;
}}

.o_portal .breadcrumb-item a:hover {{
    color: {hover_color} !important;
}}

/* ---- General Links (Frontend) ---- */
#wrapwrap a:not(.btn):not(.nav-link):not(.dropdown-item),
.o_portal a:not(.btn):not(.nav-link):not(.dropdown-item),
main a:not(.btn):not(.nav-link):not(.dropdown-item) {{
    color: {primary_color} !important;
}}

#wrapwrap a:not(.btn):not(.nav-link):not(.dropdown-item):hover,
.o_portal a:not(.btn):not(.nav-link):not(.dropdown-item):hover,
main a:not(.btn):not(.nav-link):not(.dropdown-item):hover {{
    color: {hover_color} !important;
}}

/* ---- Buttons (Frontend) ---- */
#wrapwrap .btn-primary,
.o_portal .btn-primary,
main .btn-primary {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

#wrapwrap .btn-primary:hover,
.o_portal .btn-primary:hover,
main .btn-primary:hover {{
    background-color: {hover_color} !important;
    border-color: {hover_color} !important;
    color: {text_color} !important;
}}

#wrapwrap .btn-primary:active,
#wrapwrap .btn-primary:focus,
.o_portal .btn-primary:active,
.o_portal .btn-primary:focus,
main .btn-primary:active,
main .btn-primary:focus {{
    background-color: {active_color} !important;
    border-color: {active_color} !important;
    color: {text_color} !important;
}}

#wrapwrap .btn-outline-primary,
.o_portal .btn-outline-primary,
main .btn-outline-primary {{
    color: {primary_color} !important;
    border-color: {primary_color} !important;
}}

#wrapwrap .btn-outline-primary:hover,
.o_portal .btn-outline-primary:hover,
main .btn-outline-primary:hover {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* ---- Form Inputs Focus (Frontend) ---- */
#wrapwrap .form-control:focus,
#wrapwrap .form-select:focus,
.o_portal .form-control:focus,
.o_portal .form-select:focus,
main .form-control:focus,
main .form-select:focus {{
    border-color: {primary_color} !important;
    box-shadow: 0 0 0 0.25rem {primary_color}40 !important;
}}

/* ---- Pagination (Frontend) ---- */
#wrapwrap .page-item.active .page-link,
.o_portal .page-item.active .page-link {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

#wrapwrap .page-link,
.o_portal .page-link {{
    color: {primary_color} !important;
}}

#wrapwrap .page-link:hover,
.o_portal .page-link:hover {{
    color: {hover_color} !important;
}}

/* ---- Badges (Frontend) ---- */
.o_portal .badge.text-bg-primary,
.o_portal .badge.bg-primary,
#wrapwrap .badge.text-bg-primary,
#wrapwrap .badge.bg-primary {{
    background-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* Portal status badges (Draft, Sent, Confirmed, etc.) */
.o_portal .badge.bg-info {{
    background-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* ---- Progress Bars (Frontend) ---- */
#wrapwrap .progress-bar,
.o_portal .progress-bar {{
    background-color: {primary_color} !important;
}}

/* ---- Tables (Portal) ---- */
.o_portal .table a,
.o_portal table a {{
    color: {primary_color} !important;
}}

.o_portal .table a:hover,
.o_portal table a:hover {{
    color: {hover_color} !important;
}}

/* ---- Login / Signup / Password Reset Pages ---- */
.oe_login_form .btn-primary,
.oe_signup_form .btn-primary,
.oe_reset_password_form .btn-primary,
form[action="/web/login"] .btn-primary,
form[action="/web/signup"] .btn-primary,
form[action="/web/reset_password"] .btn-primary {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

.oe_login_form .btn-primary:hover,
.oe_signup_form .btn-primary:hover,
.oe_reset_password_form .btn-primary:hover,
form[action="/web/login"] .btn-primary:hover,
form[action="/web/signup"] .btn-primary:hover,
form[action="/web/reset_password"] .btn-primary:hover {{
    background-color: {hover_color} !important;
    border-color: {hover_color} !important;
    color: {text_color} !important;
}}

/* Login form input focus */
.oe_login_form .form-control:focus,
.oe_signup_form .form-control:focus,
.oe_reset_password_form .form-control:focus {{
    border-color: {primary_color} !important;
    box-shadow: 0 0 0 0.25rem {primary_color}40 !important;
}}

/* Login page links */
.oe_login_form a,
.oe_signup_form a,
.oe_reset_password_form a {{
    color: {primary_color} !important;
}}

.oe_login_form a:hover,
.oe_signup_form a:hover,
.oe_reset_password_form a:hover {{
    color: {hover_color} !important;
}}

/* Login page btn-link buttons (Choose user / Use another user) */
.oe_login_form .btn-link,
.oe_login_form .o_user_switch_btn,
.o_user_switch .btn-link {{
    color: {primary_color} !important;
}}

.oe_login_form .btn-link:hover,
.oe_login_form .o_user_switch_btn:hover,
.o_user_switch .btn-link:hover {{
    color: {hover_color} !important;
}}

/* User switch list items */
.o_user_switch .list-group-item:hover,
.o_user_switch .list-group-item:focus {{
    background-color: {light_color} !important;
    border-color: {primary_color} !important;
}}

.o_user_switch .list-group-item:active,
.o_user_switch .list-group-item.active {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* ---- Footer ---- */
#wrapwrap footer a:hover,
footer a:hover {{
    color: {primary_color} !important;
}}

/* ---- Checkboxes & Radio Buttons (Frontend) ---- */
#wrapwrap .form-check-input:checked,
.o_portal .form-check-input:checked {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
}}

#wrapwrap .form-check-input:focus,
.o_portal .form-check-input:focus {{
    border-color: {primary_color} !important;
    box-shadow: 0 0 0 0.25rem {primary_color}40 !important;
}}

/* ---- Portal Signature ---- */
.o_portal_signature .btn-primary {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* ---- Portal Chatter ---- */
.o_portal_chatter .btn-primary {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

.o_portal_chatter a {{
    color: {primary_color} !important;
}}

.o_portal_chatter a:hover {{
    color: {hover_color} !important;
}}

/* ---- eCommerce (if Website module installed) ---- */
.oe_website_sale .btn-primary {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

.oe_website_sale .btn-primary:hover {{
    background-color: {hover_color} !important;
    border-color: {hover_color} !important;
}}

/* ---- Mobile Responsive: Portal pages ---- */
@media (max-width: 991.98px) {{
    header .navbar-collapse {{
        background-color: {primary_color} !important;
    }}

    header .navbar-collapse .nav-link {{
        color: {text_color} !important;
        border-bottom: 1px solid {hover_color};
    }}

    header .navbar-collapse .nav-link:hover {{
        background-color: {hover_color} !important;
    }}

    /* Mobile dropdown in portal navbar */
    header .navbar-collapse .dropdown-menu {{
        background-color: {hover_color} !important;
    }}

    header .navbar-collapse .dropdown-menu .dropdown-item {{
        color: {text_color} !important;
    }}

    header .navbar-collapse .dropdown-menu .dropdown-item:hover {{
        background-color: {active_color} !important;
    }}
}}

"""

        return request.make_response(
            css,
            headers=[
                ('Content-Type', 'text/css; charset=utf-8'),
                ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ('Pragma', 'no-cache'),
                ('Expires', '0'),
            ]
        )

    @http.route('/color_customizer/theme.css', type='http', auth='public', cors='*')
    def get_theme_css(self):
        """
        Return dynamic CSS with custom primary color variables.

        The CSS overrides Odoo's default brand colors with the user-configured
        primary color. Calculated variants (hover, active, light) are generated
        automatically.

        Returns:
            HTTP Response with CSS content and caching headers.
        """
        # Get configured color or fall back to default
        primary_color = request.env['ir.config_parameter'].sudo().get_param(
            'odoo_color_customizer.primary_color',
            DEFAULT_PRIMARY_COLOR
        )

        # Validate color format
        if not primary_color or not self._is_valid_hex_color(primary_color):
            primary_color = DEFAULT_PRIMARY_COLOR

        # Calculate color variants
        hover_color = self._darken_color(primary_color, 0.1)
        active_color = self._darken_color(primary_color, 0.2)
        light_color = self._lighten_color(primary_color, 0.85)
        text_color = self._get_contrast_color(primary_color)

        # Generate CSS with custom properties and critical overrides
        css = f""":root {{
    /* Custom primary color */
    --custom-primary: {primary_color};
    --custom-primary-hover: {hover_color};
    --custom-primary-active: {active_color};
    --custom-primary-light: {light_color};
    --custom-primary-text: {text_color};

    /* Override Odoo brand colors */
    --o-brand-odoo: {primary_color};
    --o-brand-primary: {primary_color};
}}

/* ============================================================================
   CRITICAL: Navbar dropdown toggle overrides
   These rules are served dynamically to ensure they override Odoo's defaults
   ============================================================================ */

/* Set CSS variable on navbar to override Odoo's fallback */
.o_main_navbar {{
    --NavBar-entry-backgroundColor: {primary_color};
    --NavBar-entry-backgroundColor--hover: {hover_color};
    --NavBar-entry-backgroundColor--focus: {hover_color};
    --NavBar-entry-backgroundColor--active: {active_color};
    border-bottom-color: {primary_color} !important;
}}

/* Dropdown toggle buttons in menu sections */
.o_main_navbar .o_menu_sections .dropdown-toggle,
.o_main_navbar .o_menu_sections .o-dropdown.dropdown-toggle,
.o_main_navbar .o_menu_sections button.dropdown-toggle,
.o_main_navbar .o_menu_sections .o-dropdown {{
    background: {primary_color} !important;
}}

.o_main_navbar .o_menu_sections .dropdown-toggle:hover,
.o_main_navbar .o_menu_sections .dropdown-toggle:focus,
.o_main_navbar .o_menu_sections .o-dropdown:hover,
.o_main_navbar .o_menu_sections .o-dropdown:focus {{
    background: {hover_color} !important;
}}

.o_main_navbar .o_menu_sections .dropdown-toggle.show,
.o_main_navbar .o_menu_sections .dropdown-toggle[aria-expanded="true"],
.o_main_navbar .o_menu_sections .o-dropdown.show,
.o_main_navbar .o_menu_sections .o-dropdown[aria-expanded="true"] {{
    background: {active_color} !important;
}}

/* Apps menu dropdown */
.o_main_navbar .o_navbar_apps_menu .dropdown-toggle,
.o_main_navbar .o_navbar_apps_menu .o-dropdown {{
    background: {primary_color} !important;
}}

.o_main_navbar .o_navbar_apps_menu .dropdown-toggle:hover,
.o_main_navbar .o_navbar_apps_menu .dropdown-toggle:focus {{
    background: {hover_color} !important;
}}

/* ============================================================================
   NOTE: Navbar TEXT colors are intentionally NOT overridden.
   Odoo's default navbar styling handles text contrast automatically.
   We only override BACKGROUND colors here, not text colors.
   Black text should remain black - only purple elements are changed.
   ============================================================================ */

/* ============================================================================
   BUG FIX 1: Email badge/tag outline color
   Elements like "123@123" and "testuser@example.com" in Settings
   ============================================================================ */
.badge.border-primary,
.badge.text-primary {{
    outline-color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 2: Focused input field border color
   When clicking any input field, the border should use primary color
   ============================================================================ */
.o_input:focus,
.o_input:focus-within,
textarea.o_input:focus,
input.o_input:focus,
.o_field_widget input:focus,
.o_field_widget textarea:focus {{
    border-color: {primary_color} !important;
    box-shadow: none !important;
}}

/* ============================================================================
   BUG FIX 3: Activity schedule arrow buttons (Inbox, Today, This Week, etc.)
   NOTE: Removed border-color and ::before overrides - Original Odoo has
   black borders, not primary color borders
   ============================================================================ */
.o_arrow_button_current {{
    background-color: {light_color} !important;
}}

/* ============================================================================
   BUG FIX 4: Calendar current day indicator (mini calendar)
   The ::before creates the circular background on today's date
   ============================================================================ */
.o_today::before,
.o_datetime_picker .o_today::before,
.o_date_item_cell.o_today::before {{
    background-color: {light_color} !important;
}}

.o_selected.o_today::before {{
    background-color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 5 & 6: View switch buttons and graph buttons (active state)
   These appear in Sales, Purchase Analysis, and other list/graph views
   ============================================================================ */
.o_switch_view.active,
.o_graph_button.active,
.btn-secondary.o_switch_view.active,
.btn-secondary.o_graph_button.active {{
    background-color: {light_color} !important;
    border-color: {primary_color} !important;
    /* NOTE: Removed color override - text should stay dark gray like Original Odoo */
}}

/* CRITICAL FIX: Override the SCSS cached rule that sets purple text on active view switches */
.o_control_panel .o_cp_switch_buttons .btn.active,
.o_control_panel .o_cp_switch_buttons .btn.btn-secondary.active {{
    color: #343a40 !important;
}}

.o_switch_view.active:hover,
.o_switch_view.active:focus,
.o_graph_button.active:hover,
.o_graph_button.active:focus {{
    background-color: {light_color} !important;
    border-color: {hover_color} !important;
}}

/* ============================================================================
   BUG FIX 7: Input field HOVER border color
   When hovering any input field, the border should use primary color
   ============================================================================ */
.form-check:hover,
.form-check:hover .form-check-input:not(:disabled) {{
    border-color: {primary_color} !important;
}}

.form-select:where(:not(:disabled)):hover {{
    border-color: {primary_color} !important;
}}

.form-switch.o_switch_toggle:hover .form-check-input:not(:disabled) {{
    border-color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 8: .btn-light active state (Toggle chatter button, etc.)
   Override Bootstrap CSS variables for btn-light active state
   ============================================================================ */
.btn-light {{
    --btn-active-bg: {light_color} !important;
    --btn-active-border-color: {primary_color} !important;
}}

.btn-light:active,
.btn-light.active,
.btn-light:focus {{
    background-color: {light_color} !important;
    border-color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 9: Calendar/DatePicker day hover and selected states
   When hovering or clicking on calendar days
   ============================================================================ */
.o_datetime_picker .o_date_item_picker .o_datetime_button.o_selected:not(.o_select_start):not(.o_select_end),
.o_datetime_picker .o_date_item_picker .o_datetime_button:hover:not(.o_select_start):not(.o_select_end),
.o_datetime_picker .o_date_item_picker .o_datetime_button.o_today:not(.o_selected):hover:not(.o_select_start):not(.o_select_end) {{
    background: {light_color} !important;
    color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 10: Tour pointer tip (guided tour tooltip)
   Override CSS variables for tour pointer background color
   ============================================================================ */
.o_tour_pointer {{
    --TourPointer__color: {primary_color} !important;
    --TourPointer__color-accent: {hover_color} !important;
}}

.o_tour_pointer .o_tour_pointer_tip {{
    background-color: {primary_color} !important;
}}

.o_tour_pointer .o_tour_pointer_tip::before {{
    border-color: {primary_color} transparent transparent transparent !important;
}}

/* ============================================================================
   BUG FIX 11: Primary link hover/focus colors
   Links with btn-primary or text-primary class
   ============================================================================ */
.btn-link.btn-primary:hover,
.btn-link.btn-primary:focus,
.btn-link.text-primary:hover,
.btn-link.text-primary:focus {{
    color: {hover_color} !important;
}}

/* ============================================================================
   BUG FIX 12: Field widget focus-within border
   Parent container when child input is focused
   ============================================================================ */
.o_field_widget:focus-within {{
    border-color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 13: Override --o-input-border-color CSS variable
   This variable controls input border color for required/focused fields
   ============================================================================ */
.o_required_modifier {{
    --o-input-border-color: {primary_color} !important;
    --o-caret-color: {primary_color} !important;
}}

.o_field_widget:focus-within {{
    --o-input-border-color: {primary_color} !important;
    --o-caret-color: {primary_color} !important;
}}

.o_field_widget:hover {{
    --o-input-border-color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 14: Calendar mini picker selected/current day colors
   Override the light purple background and purple border
   ============================================================================ */
.o_datetime_picker .o_selected:not(.o_select_start):not(.o_select_end) {{
    background: {light_color} !important;
}}

.o_datetime_picker .o_current::before,
.o_datetime_picker .o_highlighted::before,
.o_datetime_picker .o_select_start::before,
.o_datetime_picker .o_select_end::before {{
    box-shadow: {primary_color} 0px 0px 0px 1px inset !important;
}}

.o_datetime_picker .o_select_start::before,
.o_datetime_picker .o_select_end::before {{
    background: {light_color} !important;
}}

.o_datetime_picker .o_select_start:not(.o_select_end)::after,
.o_datetime_picker .o_select_end:not(.o_select_end)::after,
.o_datetime_picker .o_select_start:not(.o_select_start)::after,
.o_datetime_picker .o_select_end:not(.o_select_start)::after {{
    background: {light_color} !important;
}}

/* ============================================================================
   BUG FIX 15: Search view should NOT have box-shadow on focus
   Original Odoo only has border color change, no box-shadow
   The input INSIDE searchview also needs box-shadow: none
   ============================================================================ */
.o_searchview:focus,
.o_searchview:focus-within,
.o_searchview.form-control:focus,
.o_searchview.form-control:focus-within,
.o_searchview input,
.o_searchview input:focus,
.o_searchview_input,
.o_searchview_input:focus {{
    box-shadow: none !important;
}}

/* ============================================================================
   BUG FIX 16 (Enhanced): Form tabs (notebook) should NOT have primary color borders
   Original Odoo has gray borders: rgb(222, 226, 230) for top/sides
   Uses CSS variable override + maximum specificity selectors to beat SCSS
   ============================================================================ */

/* Override CSS variable that SCSS uses for tab border accent */
.o_notebook {{
    --notebook-link-border-color-active-accent: #dee2e6 !important;
}}

/* Maximum specificity selectors to beat SCSS cached rules (5+ classes) */
html body .o_action .o_form_view .o_notebook .nav-tabs .nav-item .nav-link.active,
.o_web_client .o_action .o_form_view .o_notebook .nav-tabs .nav-item .nav-link.active,
.o_action_manager .o_form_view .o_notebook .nav-tabs .nav-item .nav-link.active,
.o_form_view .o_notebook .nav-tabs .nav-item .nav-link.active,
.o_notebook .nav-tabs .nav-item .nav-link.active {{
    border-top-color: #dee2e6 !important;
    border-left-color: #dee2e6 !important;
    border-right-color: #dee2e6 !important;
    border-bottom-color: transparent !important;
}}

/* ============================================================================
   BUG FIX 19-22: Additional purple color overrides
   These rules provide maximum specificity to override compiled SCSS
   ============================================================================ */

/* BUG FIX 19: Combo product card selection border */
.product-card.selected {{
    border-color: {primary_color} !important;
}}

/* BUG FIX 23: Combo product card hover border */
.product-card:hover {{
    border-color: {primary_color} !important;
}}

/* BUG FIX 20: Product configurator color picker active state */
.o_sale_product_configurator_ptav_color.active {{
    border-color: {primary_color} !important;
}}

/* BUG FIX 20b: Pill-style radio buttons in configurator */
.o_sale_product_configurator_ptav_pills.active label {{
    background-color: {primary_color} !important;
    border-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* BUG FIX 21: Status bar current button */
.o_statusbar_status .o_arrow_button_current {{
    border-color: {primary_color} !important;
}}

.o_statusbar_status .o_arrow_button:hover,
.o_statusbar_status .o_arrow_button:focus {{
    border-color: {primary_color} !important;
}}

/* BUG FIX 22: Required field border in selected rows */
.o_data_row.o_selected_row > .o_data_cell.o_required_modifier:not(.o_readonly_modifier) {{
    border-bottom-color: {primary_color} !important;
}}

/* BUG FIX 19b: All links should use custom primary (with !important) */
a:not(.btn):not(.nav-link):not(.dropdown-item) {{
    color: {primary_color} !important;
}}

a:not(.btn):not(.nav-link):not(.dropdown-item):hover {{
    color: {hover_color} !important;
}}

/* ============================================================================
   BUG FIX 27: Variant price extra badges (e.g., +$111.00)
   Remove box-shadow/outline causing DOUBLE BORDER effect
   ============================================================================ */
.badge.rounded-pill.border,
.badge.border {{
    border-color: {primary_color} !important;
    box-shadow: none !important;
    outline: none !important;
    outline-color: transparent !important;
}}

.o_variant_pills_input_value .badge,
.radio_input_value .badge,
label .badge.rounded-pill.border {{
    border-color: {primary_color} !important;
    box-shadow: none !important;
    outline: none !important;
}}

/* ============================================================================
   BUG FIX 28+32+33: Combo product links in form view embedded lists
   Links inside one2many fields require form view context selectors
   Previous fixes failed because they targeted standalone list views
   BUG FIX 33: Must explicitly target .o_form_uri class which Odoo uses for form links
   Odoo core has: .o_form_view .o_form_uri {{ color: rgb(102, 89, 143) }} - purple!
   ============================================================================ */

/* CRITICAL: Override .o_form_uri which is the class on combo product links */
.o_form_view .o_form_uri,
.o_form_view .o_form_uri:visited,
.o_form_view .o_form_uri > span,
.o_form_view .o_form_uri > span:first-child,
.o_form_view .o_form_uri > span:first-child:visited {{
    color: {primary_color} !important;
}}

.o_form_view .o_form_uri:hover,
.o_form_view .o_form_uri:focus,
.o_form_view .o_form_uri.focus,
.o_form_view .o_form_uri > span:first-child:hover,
.o_form_view .o_form_uri > span:first-child:focus {{
    color: {hover_color} !important;
}}

/* Form view context - embedded one2many list links (CRITICAL for combo products) */
.o_form_view .o_field_one2many a,
.o_form_view .o_field_one2many a:visited,
.o_form_view .o_field_widget a,
.o_form_view .o_field_widget a:visited,
.o_form_view .o_list_renderer a,
.o_form_view .o_list_renderer a:visited,
.o_form_view .o_data_row a,
.o_form_view .o_data_row a:visited,
.o_form_view .o_data_cell a,
.o_form_view .o_data_cell a:visited,
.o_form_view .o_list_table a,
.o_form_view .o_list_table a:visited {{
    color: {primary_color} !important;
}}

/* Form view context - hover states */
.o_form_view .o_field_one2many a:hover,
.o_form_view .o_field_widget a:hover,
.o_form_view .o_list_renderer a:hover,
.o_form_view .o_data_row a:hover,
.o_form_view .o_data_cell a:hover,
.o_form_view .o_list_table a:hover,
.o_form_view .o_field_one2many a:visited:hover,
.o_form_view .o_field_widget a:visited:hover,
.o_form_view .o_list_renderer a:visited:hover,
.o_form_view .o_data_row a:visited:hover,
.o_form_view .o_data_cell a:visited:hover,
.o_form_view .o_list_table a:visited:hover {{
    color: {hover_color} !important;
}}

/* Standalone list view context (for regular list views outside forms) */
.o_list_renderer .o_data_row a,
.o_list_renderer .o_data_row a:visited,
.o_list_view .o_data_row a,
.o_list_view .o_data_row a:visited,
.o_data_row a,
.o_data_row a:visited,
.o_data_cell a,
.o_data_cell a:visited,
.o_list_table a,
.o_list_table a:visited {{
    color: {primary_color} !important;
}}

/* Standalone list view - hover states */
.o_list_renderer .o_data_row a:hover,
.o_list_view .o_data_row a:hover,
.o_data_row a:hover,
.o_data_cell a:hover,
.o_list_table a:hover,
.o_list_renderer .o_data_row a:visited:hover,
.o_list_view .o_data_row a:visited:hover,
.o_data_row a:visited:hover,
.o_data_cell a:visited:hover,
.o_list_table a:visited:hover {{
    color: {hover_color} !important;
}}

/* ============================================================================
   BUG FIX 29: Status bar button borders - override CSS variables + ::before
   ============================================================================ */
.o_statusbar_status {{
    --o-statusbar-border: {primary_color};
    --o-statusbar-border-active: {primary_color};
}}

.o_statusbar_status .o_arrow_button::before {{
    border-color: {primary_color} !important;
}}

.o_statusbar_status .o_arrow_button_current::before {{
    border-color: {primary_color} !important;
    background-color: {light_color} !important;
}}

.o_statusbar_status .o_arrow_button_current,
.o_statusbar_status button.o_arrow_button_current,
.o_statusbar_status .btn.o_arrow_button_current {{
    border-color: {primary_color} !important;
}}

.o_statusbar_status .o_arrow_button:hover,
.o_statusbar_status .o_arrow_button:focus,
.o_statusbar_status button.o_arrow_button:hover,
.o_statusbar_status button.o_arrow_button:focus {{
    border-color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 30: Discuss Sidebar Active/Hover States
   ============================================================================ */

/* Override CSS variables for Discuss sidebar */
.o-mail-DiscussSidebar {{
    --mail-DiscussSidebar-itemActiveBgColor: {light_color};
    --mail-DiscussSidebar-itemActiveOutlineColor: {primary_color};
}}

/* Active sidebar items */
.o-mail-DiscussSidebar-item.o-active,
.o-mail-DiscussSidebarChannel.o-active {{
    background-color: {light_color} !important;
    outline-color: {primary_color} !important;
}}

/* Hover state for sidebar items */
.o-mail-DiscussSidebar-item:hover,
.o-mail-DiscussSidebarChannel:hover {{
    background-color: {light_color} !important;
    outline-color: {primary_color} !important;
}}

/* Quick search button active state */
.o-mail-DiscussSidebarCategories-quickSearchBtn.o-active {{
    background-color: {primary_color} !important;
    color: {text_color} !important;
}}

/* Quick search input focus */
.o-mail-DiscussSidebarQuickSearchInput.o-active {{
    outline-color: {primary_color} !important;
}}

/* Category headers with icons */
.o-mail-DiscussSidebarCategory-toggler:hover {{
    color: {primary_color} !important;
}}

/* ============================================================================
   BUG FIX 34: Frontend Editor Launcher (Triangle + Apps Button)
   The triangle and square launcher on website frontend uses $o-enterprise-color
   Source: website/static/src/scss/website.ui.scss lines 14-57
   ============================================================================ */
.o_frontend_to_backend_nav::before {{
    border-top-color: {primary_color} !important;
    border-left-color: {primary_color} !important;
}}

.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn {{
    background-color: {primary_color} !important;
}}

.o_frontend_to_backend_nav .o_frontend_to_backend_apps_btn:hover {{
    background-color: {hover_color} !important;
}}
"""

        return request.make_response(
            css,
            headers=[
                ('Content-Type', 'text/css; charset=utf-8'),
                ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ('Pragma', 'no-cache'),
                ('Expires', '0'),
            ]
        )

    def _is_valid_hex_color(self, color):
        """Check if string is a valid hex color."""
        if not color or len(color) != 7 or color[0] != '#':
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False

    def _hex_to_rgb(self, hex_color):
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color string."""
        r, g, b = [max(0, min(255, int(c))) for c in rgb]
        return f'#{r:02x}{g:02x}{b:02x}'

    def _darken_color(self, hex_color, amount):
        """
        Darken a hex color by a percentage.

        Args:
            hex_color: Hex color string (e.g., '#71639e')
            amount: Percentage to darken (0.0 to 1.0)

        Returns:
            Darkened hex color string
        """
        r, g, b = self._hex_to_rgb(hex_color)
        factor = 1 - amount
        return self._rgb_to_hex((r * factor, g * factor, b * factor))

    def _lighten_color(self, hex_color, amount):
        """
        Lighten a hex color by a percentage.

        Args:
            hex_color: Hex color string (e.g., '#71639e')
            amount: Percentage to lighten (0.0 to 1.0)

        Returns:
            Lightened hex color string
        """
        r, g, b = self._hex_to_rgb(hex_color)
        return self._rgb_to_hex((
            r + (255 - r) * amount,
            g + (255 - g) * amount,
            b + (255 - b) * amount
        ))

    def _get_contrast_color(self, hex_color):
        """
        Return white or black based on background luminance.

        Uses relative luminance formula to determine optimal text color
        for accessibility.

        Args:
            hex_color: Background hex color string

        Returns:
            '#ffffff' for dark backgrounds, '#000000' for light backgrounds
        """
        r, g, b = self._hex_to_rgb(hex_color)
        # Calculate relative luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return '#ffffff' if luminance < 0.5 else '#000000'
