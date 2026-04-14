# -*- coding: utf-8 -*-
"""
Template rendering tests for woow_portal_enhanced.

Covers:
  - Portal home template structure
  - Admin banner conditional rendering
  - Bell icon in header
  - User dropdown links (Return to Backend, My Account)
  - Module grid CSS classes
  - Drawer structure
  - CSS and JS assets loaded
"""

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPortalTemplates(HttpCase):
    """Test QWeb template rendering and conditional elements."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Template Test Portal',
            'login': 'tmpl_portal',
            'password': 'tmpl_portal',
            'email': 'tmpl_portal@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def _get_portal_home(self, login, password):
        """Helper to fetch portal home as specific user."""
        self.authenticate(login, password)
        return self.url_open('/my/home')

    # ------------------------------------------------------------------
    # 1. CSS asset loaded
    # ------------------------------------------------------------------

    def test_01_css_asset_loaded(self):
        """Custom CSS should be loaded via web.assets_frontend."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        # The CSS is bundled into web.assets_frontend.min.css
        # We verify our custom classes are usable in the HTML
        self.assertIn('wpe-search-bar', res.text)

    # ------------------------------------------------------------------
    # 2. JS asset loaded
    # ------------------------------------------------------------------

    def test_02_js_asset_loaded(self):
        """Custom JS should be loaded via web.assets_frontend."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        # JS is bundled, so we check for DOM elements that JS targets
        self.assertIn('wpe_module_search', res.text)
        self.assertIn('wpe_drawer', res.text)

    # ------------------------------------------------------------------
    # 3. Admin banner — conditional rendering
    # ------------------------------------------------------------------

    def test_03_admin_banner_visible_for_internal(self):
        """Internal user should see admin banner."""
        res = self._get_portal_home('admin', 'admin')
        self.assertIn('wpe-admin-banner', res.text)
        self.assertIn('/odoo', res.text)  # Return to backend link

    def test_04_admin_banner_hidden_for_portal(self):
        """Portal user should NOT see admin banner."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertNotIn('wpe-admin-banner', res.text)

    # ------------------------------------------------------------------
    # 4. Bell icon in header
    # ------------------------------------------------------------------

    def test_05_bell_icon_present(self):
        """Bell icon should be in the navbar for all authenticated users."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe_bell_trigger', res.text)
        self.assertIn('fa-bell-o', res.text)

    def test_06_bell_badge_hidden_by_default(self):
        """Badge should start with d-none class."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        # The badge span should have d-none
        self.assertRegex(res.text, r'wpe-badge[^>]*d-none')

    # ------------------------------------------------------------------
    # 5. User dropdown links
    # ------------------------------------------------------------------

    def test_07_admin_dropdown_has_backend_and_portal_links(self):
        """Admin dropdown should have Apps, Return to Backend, My Account, Logout."""
        res = self._get_portal_home('admin', 'admin')
        self.assertIn('o_backend_user_dropdown_link', res.text)   # Apps
        self.assertIn('wpe_return_backend_link', res.text)         # Return to Backend
        self.assertIn('o_logout', res.text)                        # Logout

    def test_08_portal_dropdown_has_no_backend_link(self):
        """Portal user dropdown should NOT have backend links."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertNotIn('o_backend_user_dropdown_link', res.text)
        self.assertNotIn('wpe_return_backend_link', res.text)

    def test_09_portal_dropdown_has_logout(self):
        """Portal user dropdown should have logout link."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('o_logout', res.text)

    # ------------------------------------------------------------------
    # 6. Module grid structure
    # ------------------------------------------------------------------

    def test_10_module_grid_structure(self):
        """Module grid should have expected CSS structure."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe-module-grid', res.text)
        self.assertIn('o_portal_docs', res.text)
        self.assertIn('o_portal_category', res.text)

    def test_11_connection_security_card(self):
        """Connection & Security card should always be present."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('/my/security', res.text)

    # ------------------------------------------------------------------
    # 7. Notification drawer structure
    # ------------------------------------------------------------------

    def test_12_drawer_structure(self):
        """Drawer should have header, tabs, body, and backdrop."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe_drawer', res.text)
        self.assertIn('wpe_drawer_backdrop', res.text)
        self.assertIn('wpe_drawer_close', res.text)
        self.assertIn('wpe-drawer-tabs', res.text)
        self.assertIn('wpe_drawer_body', res.text)

    def test_13_drawer_tabs(self):
        """Drawer should have 3 tab buttons."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        # Count occurrences of wpe-tab-btn
        count = res.text.count('wpe-tab-btn')
        self.assertEqual(count, 3, "Should have exactly 3 tab buttons")

    def test_14_drawer_tab_data_attributes(self):
        """Tabs should have data-tab attributes for all/todo/system."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('data-tab="all"', res.text)
        self.assertIn('data-tab="todo"', res.text)
        self.assertIn('data-tab="system"', res.text)

    # ------------------------------------------------------------------
    # 8. Search bar structure
    # ------------------------------------------------------------------

    def test_15_search_bar_structure(self):
        """Search bar should have input group with icon and input."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe-search-bar', res.text)
        self.assertIn('fa-search', res.text)
        self.assertIn('wpe_module_search', res.text)

    # ------------------------------------------------------------------
    # 9. Notification preview section
    # ------------------------------------------------------------------

    def test_16_notification_preview_section(self):
        """Notification preview section should exist."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe-notification-preview', res.text)
        self.assertIn('wpe_open_drawer_link', res.text)

    # ------------------------------------------------------------------
    # 10. HTML structure integrity
    # ------------------------------------------------------------------

    def test_17_page_has_portal_wrap(self):
        """Page should have o_portal class on wrapwrap."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('o_portal', res.text)

    def test_18_page_is_valid_html(self):
        """Page should have basic HTML structure."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('<!DOCTYPE html>', res.text)
        self.assertIn('</html>', res.text)
        self.assertIn('<head>', res.text)
        self.assertIn('<body>', res.text)
