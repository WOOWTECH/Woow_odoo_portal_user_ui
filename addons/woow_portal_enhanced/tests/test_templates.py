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
  - Notification preview section (mail.notification based)
  - Notification page structure (3 tabs + activity for internal)
  - Detail modal markup
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

    @classmethod
    def _create_notification(cls, partner, subject='Test Notification',
                             message_type='notification', is_read=False):
        """Helper to create a mail.message + mail.notification pair."""
        msg = cls.env['mail.message'].sudo().create({
            'model': 'res.partner',
            'res_id': partner.id,
            'subject': subject,
            'body': '<p>%s body</p>' % subject,
            'message_type': message_type,
            'subtype_id': cls.env.ref('mail.mt_comment').id,
            'author_id': partner.id,
        })
        return cls.env['mail.notification'].sudo().create({
            'mail_message_id': msg.id,
            'res_partner_id': partner.id,
            'notification_type': 'inbox',
            'is_read': is_read,
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
    # 3. Admin banner removed (no longer shown for any user)
    # ------------------------------------------------------------------

    def test_03_no_admin_banner_for_internal(self):
        """Internal user should NOT see admin banner (removed)."""
        res = self._get_portal_home('admin', 'admin')
        self.assertNotIn('wpe-admin-banner', res.text)

    def test_04_no_admin_banner_for_portal(self):
        """Portal user should NOT see admin banner (removed)."""
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
    # 6. User dropdown links (Return to Backend removed)
    # ------------------------------------------------------------------

    def test_07_admin_dropdown_no_return_backend(self):
        """Admin dropdown should NOT have Return to Backend (removed)."""
        res = self._get_portal_home('admin', 'admin')
        self.assertNotIn('wpe_return_backend_link', res.text)
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

    def test_12b_notification_preview_with_data(self):
        """Preview should show notification content when data exists."""
        partner = self.portal_user.partner_id
        self._create_notification(
            partner, subject='Template Preview Test',
            message_type='notification', is_read=False)

        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertIn('Template Preview Test', res.text,
                      "Notification subject should appear in preview")

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
        """Notification page should have tabs and empty state."""
        self.authenticate('tmpl_portal', 'tmpl_portal')
        res = self.url_open('/my/notifications')
        self.assertEqual(res.status_code, 200)
        self.assertIn('wpe-notif-tabs', res.text)
        # Empty state (no notifications for this user)
        self.assertIn('wpe-notif-empty', res.text)

    def test_14b_notification_page_tabs_portal(self):
        """Portal user notification page should have message/notification tabs."""
        self.authenticate('tmpl_portal', 'tmpl_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=all', res.text)
        self.assertIn('tab=message', res.text)
        self.assertIn('tab=notification', res.text)
        # Portal should NOT have activity tab
        self.assertNotIn('tab=activity', res.text)

    def test_14c_notification_page_tabs_admin(self):
        """Admin notification page should have all 4 tabs including activity."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=all', res.text)
        self.assertIn('tab=message', res.text)
        self.assertIn('tab=notification', res.text)
        self.assertIn('tab=activity', res.text)

    def test_15_notification_page_with_notification_cards(self):
        """Notification page should render swipeable card wrappers."""
        partner = self.portal_user.partner_id
        self._create_notification(
            partner, subject='Template Notif Test',
            message_type='notification', is_read=False)

        self.authenticate('tmpl_portal', 'tmpl_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-card-wrapper', res.text)
        self.assertIn('wpe-notif-swipe-bg', res.text)
        self.assertIn('wpe-notif-card', res.text)
        self.assertIn('Template Notif Test', res.text)
        self.assertIn('data-notif-id', res.text,
                      "Notification card should have data-notif-id attribute")
        self.assertIn('data-item-type="notification"', res.text,
                      "Notification card should have data-item-type=notification")

    # ------------------------------------------------------------------
    # 11. Detail modal markup
    # ------------------------------------------------------------------

    def test_16_detail_modal_markup(self):
        """Notification page should contain the detail modal markup."""
        self.authenticate('tmpl_portal', 'tmpl_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe_notif_modal_overlay', res.text,
                      "Modal overlay element should exist")
        self.assertIn('wpe_notif_modal', res.text,
                      "Modal container should exist")
        self.assertIn('wpe_modal_title', res.text,
                      "Modal title element should exist")
        self.assertIn('wpe_modal_close', res.text,
                      "Modal close button should exist")
        self.assertIn('wpe_modal_body', res.text,
                      "Modal body element should exist")
        self.assertIn('wpe_modal_doc_link', res.text,
                      "Modal document link should exist")
        self.assertIn('wpe_modal_action_btn', res.text,
                      "Modal action button should exist")

    # ------------------------------------------------------------------
    # 12. HTML structure integrity
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

    # ------------------------------------------------------------------
    # 13. Footer hidden (Copyright / Powered by Odoo removed)
    # ------------------------------------------------------------------

    def test_19_footer_hidden(self):
        """Footer with Copyright / Powered by should be hidden."""
        res = self._get_portal_home('tmpl_portal', 'tmpl_portal')
        self.assertNotIn('Powered by', res.text,
                         "Footer 'Powered by' should be hidden")

    def test_19b_footer_hidden_for_admin(self):
        """Footer should also be hidden for admin users."""
        res = self._get_portal_home('admin', 'admin')
        self.assertNotIn('Powered by', res.text)

    # ------------------------------------------------------------------
    # 14. Return button enlarged on notification page
    # ------------------------------------------------------------------

    def test_20_return_button_has_enlarge_class(self):
        """Return button on notification page should have wpe-notif-return-btn class."""
        self.authenticate('tmpl_portal', 'tmpl_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-return-btn', res.text,
                       "Return button should have the enlargement CSS class")
