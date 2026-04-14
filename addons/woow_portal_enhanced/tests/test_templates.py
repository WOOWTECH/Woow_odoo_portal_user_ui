# -*- coding: utf-8 -*-
"""
Template rendering tests for woow_portal_enhanced.

Covers:
  - Portal home template structure
  - Admin banner conditional rendering
  - No bell icon (removed)
  - No drawer (removed)
  - User dropdown links (Return to Backend, My Account)
  - Module grid CSS classes
  - Notification preview section
  - Notification page structure
  - CSS and JS assets loaded
"""

from odoo import fields
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
    # 4. No bell icon (removed in refactor)
    # ------------------------------------------------------------------

    def test_05_no_bell_icon(self):
        """Bell icon should NOT be in the page (removed)."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertNotIn('wpe_bell_trigger', res.text)
        self.assertNotIn('wpe-badge', res.text)

    # ------------------------------------------------------------------
    # 5. No drawer (removed in refactor)
    # ------------------------------------------------------------------

    def test_06_no_drawer(self):
        """Notification drawer should NOT be in the page (removed)."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertNotIn('wpe_drawer', res.text)
        self.assertNotIn('wpe_drawer_backdrop', res.text)
        self.assertNotIn('wpe_drawer_close', res.text)
        self.assertNotIn('wpe-drawer-tabs', res.text)
        self.assertNotIn('wpe_drawer_body', res.text)

    # ------------------------------------------------------------------
    # 6. User dropdown links
    # ------------------------------------------------------------------

    def test_07_admin_dropdown_has_backend_and_portal_links(self):
        """Admin dropdown should have Apps, Return to Backend, Logout."""
        res = self._get_portal_home('admin', 'admin')
        self.assertIn('wpe_return_backend_link', res.text)
        self.assertIn('o_logout', res.text)

    def test_08_portal_dropdown_has_no_backend_link(self):
        """Portal user dropdown should NOT have backend links."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertNotIn('wpe_return_backend_link', res.text)

    def test_09_portal_dropdown_has_logout(self):
        """Portal user dropdown should have logout link."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('o_logout', res.text)

    # ------------------------------------------------------------------
    # 7. Module grid structure
    # ------------------------------------------------------------------

    def test_10_module_grid_structure(self):
        """Module grid should have expected CSS structure."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe_module_grid', res.text)
        self.assertIn('o_portal_docs', res.text)

    def test_11_connection_security_card(self):
        """Connection & Security card should always be present."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('/my/security', res.text)

    # ------------------------------------------------------------------
    # 8. Notification preview section
    # ------------------------------------------------------------------

    def test_12_notification_preview_section(self):
        """Notification preview section should exist with link to full page."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe-notification-preview', res.text)
        self.assertIn('wpe-view-all-link', res.text)
        self.assertIn('/my/notifications', res.text)

    # ------------------------------------------------------------------
    # 9. Search bar structure
    # ------------------------------------------------------------------

    def test_13_search_bar_structure(self):
        """Search bar should have input group with icon and input."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('wpe-search-bar', res.text)
        self.assertIn('fa-search', res.text)
        self.assertIn('wpe_module_search', res.text)

    # ------------------------------------------------------------------
    # 10. Notification page structure
    # ------------------------------------------------------------------

    def test_14_notification_page_structure(self):
        """Notification page should have tabs and swipe hint."""
        self.authenticate('tmpl_portal', 'tmpl_portal')
        res = self.url_open('/my/notifications')
        self.assertEqual(res.status_code, 200)
        self.assertIn('wpe-notif-tabs', res.text)
        # Empty state (no activities for this user)
        self.assertIn('wpe-notif-empty', res.text)

    def test_15_notification_page_with_activities(self):
        """Notification page should render swipeable card wrappers."""
        partner = self.portal_user.partner_id
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': partner.id,
            'user_id': self.portal_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Template Notif Test',
            'date_deadline': fields.Date.today(),
        })

        self.authenticate('tmpl_portal', 'tmpl_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-card-wrapper', res.text)
        self.assertIn('wpe-notif-swipe-bg', res.text)
        self.assertIn('wpe-notif-card', res.text)
        self.assertIn('Template Notif Test', res.text)
        self.assertIn('wpe_swipe_hint', res.text)

    # ------------------------------------------------------------------
    # 11. HTML structure integrity
    # ------------------------------------------------------------------

    def test_16_page_has_portal_wrap(self):
        """Page should have o_portal class on wrapwrap."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('o_portal', res.text)

    def test_17_page_is_valid_html(self):
        """Page should have basic HTML structure."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('<!DOCTYPE html>', res.text)
        self.assertIn('</html>', res.text)
        self.assertIn('<head>', res.text)
        self.assertIn('<body>', res.text)
