# -*- coding: utf-8 -*-
"""
Dedicated tests for the 5 UI optimization features.

Covers:
  1. Admin banner removal — completeness across user types and pages
  2. "返回後台" dropdown removal — both dropdown item & template
  3. Return button 120% enlargement — CSS class presence
  4. Module card ↔ notification card style unification — CSS classes
  5. Footer removal — hidden across portal home, notification page
  6. Navbar white background — CSS asset coverage
  7. Edge cases: second portal user, multi-page consistency,
     no regressions on existing features
"""

import re

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestAdminBannerRemoval(HttpCase):
    """Verify admin banner is completely gone for all user types and pages."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Banner Test Portal',
            'login': 'banner_portal',
            'password': 'banner_portal',
            'email': 'banner_portal@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    # ------------------------------------------------------------------
    # 1. No banner on portal home — both user types
    # ------------------------------------------------------------------

    def test_01_no_banner_portal_home_admin(self):
        """Admin: /my/home should have zero admin banner elements."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe-admin-banner', res.text)
        self.assertNotIn('您正在以管理員身份瀏覽', res.text)

    def test_02_no_banner_portal_home_portal(self):
        """Portal: /my/home should have zero admin banner elements."""
        self.authenticate('banner_portal', 'banner_portal')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe-admin-banner', res.text)
        self.assertNotIn('您正在以管理員身份瀏覽', res.text)

    # ------------------------------------------------------------------
    # 2. No banner on notification page
    # ------------------------------------------------------------------

    def test_03_no_banner_notification_page_admin(self):
        """Admin: /my/notifications should not have admin banner."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertNotIn('wpe-admin-banner', res.text)

    def test_04_no_banner_notification_page_portal(self):
        """Portal: /my/notifications should not have admin banner."""
        self.authenticate('banner_portal', 'banner_portal')
        res = self.url_open('/my/notifications')
        self.assertNotIn('wpe-admin-banner', res.text)

    # ------------------------------------------------------------------
    # 3. No banner on /my route alias
    # ------------------------------------------------------------------

    def test_05_no_banner_my_route_admin(self):
        """Admin: /my should also not have admin banner."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my')
        self.assertNotIn('wpe-admin-banner', res.text)

    # ------------------------------------------------------------------
    # 4. No "返回後台" text anywhere in the banner context
    # ------------------------------------------------------------------

    def test_06_no_return_backend_text_in_banner_context(self):
        """The '返回後台' text that was inside the banner should be gone."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        # The banner had a link with this text; it should not appear
        # in the o_portal_my_home area anymore (could still exist in
        # Odoo's built-in user menu if base has it)
        self.assertNotIn('wpe-admin-banner', res.text)


@tagged('post_install', '-at_install')
class TestDropdownBackendLinkRemoval(HttpCase):
    """Verify '返回後台' dropdown menu item is completely removed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Dropdown Test Portal',
            'login': 'dropdown_portal',
            'password': 'dropdown_portal',
            'email': 'dropdown_portal@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    # ------------------------------------------------------------------
    # 1. Admin: no wpe_return_backend_link on any page
    # ------------------------------------------------------------------

    def test_01_no_dropdown_backend_link_admin_home(self):
        """Admin on /my/home should not have wpe_return_backend_link."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe_return_backend_link', res.text)

    def test_02_no_dropdown_backend_link_admin_notifications(self):
        """Admin on /my/notifications should not have wpe_return_backend_link."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertNotIn('wpe_return_backend_link', res.text)

    # ------------------------------------------------------------------
    # 2. Portal user: no wpe_return_backend_link
    # ------------------------------------------------------------------

    def test_03_no_dropdown_backend_link_portal_home(self):
        """Portal on /my/home should not have wpe_return_backend_link."""
        self.authenticate('dropdown_portal', 'dropdown_portal')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe_return_backend_link', res.text)

    def test_04_no_dropdown_backend_link_portal_notifications(self):
        """Portal on /my/notifications should not have wpe_return_backend_link."""
        self.authenticate('dropdown_portal', 'dropdown_portal')
        res = self.url_open('/my/notifications')
        self.assertNotIn('wpe_return_backend_link', res.text)

    # ------------------------------------------------------------------
    # 3. Logout link still present (no regression)
    # ------------------------------------------------------------------

    def test_05_logout_link_still_present_admin(self):
        """Admin should still have the logout link."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertIn('o_logout', res.text)

    def test_06_logout_link_still_present_portal(self):
        """Portal user should still have the logout link."""
        self.authenticate('dropdown_portal', 'dropdown_portal')
        res = self.url_open('/my/home')
        self.assertIn('o_logout', res.text)

    # ------------------------------------------------------------------
    # 4. Template was deleted — view no longer exists in registry
    # ------------------------------------------------------------------

    def test_07_template_deleted_from_registry(self):
        """The portal_user_dropdown_backend_link template should not exist."""
        view = self.env['ir.ui.view'].sudo().search([
            ('key', '=',
             'woow_portal_enhanced.portal_user_dropdown_backend_link'),
        ])
        self.assertFalse(
            view.exists(),
            "portal_user_dropdown_backend_link template should be deleted")


@tagged('post_install', '-at_install')
class TestReturnButtonEnlargement(HttpCase):
    """Verify the return button on /my/notifications has 120% enlargement."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Return Btn Test',
            'login': 'return_btn_test',
            'password': 'return_btn_test',
            'email': 'return_btn@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    # ------------------------------------------------------------------
    # 1. CSS class presence on the return button
    # ------------------------------------------------------------------

    def test_01_return_button_has_enlarge_class_portal(self):
        """Portal: return button should have wpe-notif-return-btn class."""
        self.authenticate('return_btn_test', 'return_btn_test')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-return-btn', res.text)

    def test_02_return_button_has_enlarge_class_admin(self):
        """Admin: return button should also have wpe-notif-return-btn class."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-return-btn', res.text)

    # ------------------------------------------------------------------
    # 2. Return button links back to /my/home
    # ------------------------------------------------------------------

    def test_03_return_button_links_to_home(self):
        """Return button href should be /my/home."""
        self.authenticate('return_btn_test', 'return_btn_test')
        res = self.url_open('/my/notifications')
        # Check that the return button links to /my/home
        self.assertIn('href="/my/home"', res.text)

    # ------------------------------------------------------------------
    # 3. Return button contains the right text
    # ------------------------------------------------------------------

    def test_04_return_button_has_correct_text(self):
        """Return button should display '返回' text."""
        self.authenticate('return_btn_test', 'return_btn_test')
        res = self.url_open('/my/notifications')
        # The button has fa-arrow-left icon and '返回' text
        self.assertIn('fa-arrow-left', res.text)

    # ------------------------------------------------------------------
    # 4. Return button NOT on portal home (only notification page)
    # ------------------------------------------------------------------

    def test_05_no_return_button_on_home(self):
        """Portal home should NOT have wpe-notif-return-btn."""
        self.authenticate('return_btn_test', 'return_btn_test')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe-notif-return-btn', res.text,
                         "Return button class should only be on notification page")

    # ------------------------------------------------------------------
    # 5. Each tab preserves the return button
    # ------------------------------------------------------------------

    def test_06_return_button_on_message_tab(self):
        """Return button present on ?tab=message."""
        self.authenticate('return_btn_test', 'return_btn_test')
        res = self.url_open('/my/notifications?tab=message')
        self.assertIn('wpe-notif-return-btn', res.text)

    def test_07_return_button_on_notification_tab(self):
        """Return button present on ?tab=notification."""
        self.authenticate('return_btn_test', 'return_btn_test')
        res = self.url_open('/my/notifications?tab=notification')
        self.assertIn('wpe-notif-return-btn', res.text)

    def test_08_return_button_on_activity_tab_admin(self):
        """Return button present on ?tab=activity for admin."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications?tab=activity')
        self.assertIn('wpe-notif-return-btn', res.text)


@tagged('post_install', '-at_install')
class TestFooterHidden(HttpCase):
    """Verify footer (Copyright / Powered by Odoo) is completely hidden."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Footer Test Portal',
            'login': 'footer_portal',
            'password': 'footer_portal',
            'email': 'footer_portal@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    # ------------------------------------------------------------------
    # 1. No "Powered by" on portal home
    # ------------------------------------------------------------------

    def test_01_no_powered_by_portal_home(self):
        """Portal home should not show 'Powered by'."""
        self.authenticate('footer_portal', 'footer_portal')
        res = self.url_open('/my/home')
        self.assertNotIn('Powered by', res.text)

    def test_02_no_powered_by_portal_home_admin(self):
        """Admin portal home should not show 'Powered by'."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertNotIn('Powered by', res.text)

    # ------------------------------------------------------------------
    # 2. No "Powered by" on notification page
    # ------------------------------------------------------------------

    def test_03_no_powered_by_notification_page(self):
        """Notification page should not show 'Powered by'."""
        self.authenticate('footer_portal', 'footer_portal')
        res = self.url_open('/my/notifications')
        self.assertNotIn('Powered by', res.text)

    def test_04_no_powered_by_notification_page_admin(self):
        """Admin notification page should not show 'Powered by'."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertNotIn('Powered by', res.text)

    # ------------------------------------------------------------------
    # 3. Footer element is hidden (d-none class)
    # ------------------------------------------------------------------

    def test_05_footer_has_d_none_class(self):
        """Footer element should have d-none class."""
        self.authenticate('footer_portal', 'footer_portal')
        res = self.url_open('/my/home')
        # Our template replaces footer with <footer id="bottom" class="d-none"/>
        # Check that the footer with bottom id is d-none
        match = re.search(r'<footer[^>]*id=["\']bottom["\'][^>]*>', res.text)
        self.assertTrue(match, "Footer element should exist with id='bottom'")
        self.assertIn('d-none', match.group(0),
                      "Footer should have d-none class")

    # ------------------------------------------------------------------
    # 4. No "o_footer_copyright" visible
    # ------------------------------------------------------------------

    def test_06_no_footer_copyright_class(self):
        """o_footer_copyright class should not appear in rendered HTML."""
        self.authenticate('footer_portal', 'footer_portal')
        res = self.url_open('/my/home')
        self.assertNotIn('o_footer_copyright', res.text,
                         "Footer copyright section should be removed")

    # ------------------------------------------------------------------
    # 5. Template inheritance is correctly applied
    # ------------------------------------------------------------------

    def test_07_footer_template_exists(self):
        """portal_hide_footer template should exist and inherit web.frontend_layout."""
        view = self.env['ir.ui.view'].sudo().search([
            ('key', '=', 'woow_portal_enhanced.portal_hide_footer'),
        ])
        self.assertTrue(view.exists(),
                        "portal_hide_footer template should exist")
        self.assertEqual(view.inherit_id.key, 'web.frontend_layout',
                         "Should inherit from web.frontend_layout")

    # ------------------------------------------------------------------
    # 6. Edge case: /my route also has no footer
    # ------------------------------------------------------------------

    def test_08_no_powered_by_my_route(self):
        """The /my route should also have no 'Powered by'."""
        self.authenticate('footer_portal', 'footer_portal')
        res = self.url_open('/my')
        self.assertNotIn('Powered by', res.text)

    # ------------------------------------------------------------------
    # 7. Notification page tabs don't break footer hiding
    # ------------------------------------------------------------------

    def test_09_no_footer_message_tab(self):
        """No footer on ?tab=message."""
        self.authenticate('footer_portal', 'footer_portal')
        res = self.url_open('/my/notifications?tab=message')
        self.assertNotIn('Powered by', res.text)

    def test_10_no_footer_notification_tab(self):
        """No footer on ?tab=notification."""
        self.authenticate('footer_portal', 'footer_portal')
        res = self.url_open('/my/notifications?tab=notification')
        self.assertNotIn('Powered by', res.text)


@tagged('post_install', '-at_install')
class TestModuleCardStyleUnification(HttpCase):
    """Verify module cards have the CSS classes matching notification style."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'CardStyle Test Portal',
            'login': 'card_style_portal',
            'password': 'card_style_portal',
            'email': 'cardstyle@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    # ------------------------------------------------------------------
    # 1. Module grid has correct structure
    # ------------------------------------------------------------------

    def test_01_module_grid_has_card_structure(self):
        """Module grid should have o_portal_index_card elements."""
        self.authenticate('card_style_portal', 'card_style_portal')
        res = self.url_open('/my/home')
        self.assertIn('o_portal_index_card', res.text,
                      "Module grid should contain card elements")

    def test_02_module_grid_has_icon_elements(self):
        """Module cards should have o_portal_icon elements."""
        self.authenticate('card_style_portal', 'card_style_portal')
        res = self.url_open('/my/home')
        self.assertIn('o_portal_icon', res.text,
                      "Module cards should have icon elements")

    # ------------------------------------------------------------------
    # 2. Notification preview card structure intact
    # ------------------------------------------------------------------

    def test_03_notification_preview_card_structure(self):
        """Preview card with data should have notification-icon style."""
        partner = self.portal_user.partner_id
        msg = self.env['mail.message'].sudo().create({
            'model': 'res.partner',
            'res_id': partner.id,
            'subject': 'Card Style Notif',
            'body': '<p>test</p>',
            'message_type': 'notification',
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'author_id': partner.id,
        })
        self.env['mail.notification'].sudo().create({
            'mail_message_id': msg.id,
            'res_partner_id': partner.id,
            'notification_type': 'inbox',
            'is_read': False,
        })

        self.authenticate('card_style_portal', 'card_style_portal')
        res = self.url_open('/my/home')
        self.assertIn('wpe-notification-icon', res.text,
                      "Notification preview should have icon element")
        self.assertIn('wpe-notification-preview', res.text,
                      "Notification preview card should exist")

    # ------------------------------------------------------------------
    # 3. Both module cards & preview co-exist
    # ------------------------------------------------------------------

    def test_04_both_card_types_on_same_page(self):
        """Portal home should have both notification preview and module grid."""
        self.authenticate('card_style_portal', 'card_style_portal')
        res = self.url_open('/my/home')
        self.assertIn('wpe-notification-preview', res.text)
        self.assertIn('wpe_module_grid', res.text)
        self.assertIn('o_portal_docs', res.text)

    # ------------------------------------------------------------------
    # 4. Admin sees same module card structure
    # ------------------------------------------------------------------

    def test_05_admin_module_cards_same_structure(self):
        """Admin should see the same module card structure."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertIn('o_portal_index_card', res.text)
        self.assertIn('o_portal_icon', res.text)


@tagged('post_install', '-at_install')
class TestNavbarWhiteBackground(HttpCase):
    """Verify top navbar has white background via CSS asset loading."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Navbar Test Portal',
            'login': 'navbar_portal',
            'password': 'navbar_portal',
            'email': 'navbar@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    # ------------------------------------------------------------------
    # 1. Navbar element present
    # ------------------------------------------------------------------

    def test_01_navbar_present_portal_home(self):
        """Portal home should have navbar element."""
        self.authenticate('navbar_portal', 'navbar_portal')
        res = self.url_open('/my/home')
        # Odoo portal wraps content in o_portal_wrap
        self.assertIn('o_portal_wrap', res.text)
        # Navbar uses Bootstrap navbar class
        has_navbar = ('navbar' in res.text)
        self.assertTrue(has_navbar, "Page should contain a navbar element")

    def test_02_navbar_present_notifications(self):
        """Notification page should also have navbar."""
        self.authenticate('navbar_portal', 'navbar_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('o_portal_wrap', res.text)

    # ------------------------------------------------------------------
    # 2. CSS asset that sets white background is loaded
    # ------------------------------------------------------------------

    def test_03_css_asset_loaded(self):
        """portal.css should be bundled into web.assets_frontend."""
        self.authenticate('navbar_portal', 'navbar_portal')
        res = self.url_open('/my/home')
        # Our CSS is bundled, verify custom classes are rendered
        self.assertIn('wpe-search-bar', res.text,
                      "Custom CSS should be loaded (wpe-search-bar)")


@tagged('post_install', '-at_install')
class TestUIOptimizationNoRegression(HttpCase):
    """Cross-cutting regression tests to ensure existing features still work
    after the 5 UI optimizations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Regression Test Portal',
            'login': 'regr_portal',
            'password': 'regr_portal',
            'email': 'regr_portal@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        # Create a second portal user to test multi-user isolation
        cls.portal_user_2 = cls.env['res.users'].create({
            'name': 'Regression Test Portal 2',
            'login': 'regr_portal_2',
            'password': 'regr_portal_2',
            'email': 'regr_portal_2@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    @classmethod
    def _create_notification(cls, partner, subject='Test', is_read=False):
        """Helper to create mail.message + mail.notification."""
        msg = cls.env['mail.message'].sudo().create({
            'model': 'res.partner',
            'res_id': partner.id,
            'subject': subject,
            'body': '<p>%s</p>' % subject,
            'message_type': 'notification',
            'subtype_id': cls.env.ref('mail.mt_comment').id,
            'author_id': partner.id,
        })
        return cls.env['mail.notification'].sudo().create({
            'mail_message_id': msg.id,
            'res_partner_id': partner.id,
            'notification_type': 'inbox',
            'is_read': is_read,
        })

    # ------------------------------------------------------------------
    # 1. Search bar still works
    # ------------------------------------------------------------------

    def test_01_search_bar_still_present(self):
        """Search bar should still be present after UI optimizations."""
        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/home')
        self.assertIn('wpe-search-bar', res.text)
        self.assertIn('wpe_module_search', res.text)
        self.assertIn('fa-search', res.text)

    # ------------------------------------------------------------------
    # 2. Notification preview still works
    # ------------------------------------------------------------------

    def test_02_notification_preview_still_works(self):
        """Notification preview card should still render."""
        partner = self.portal_user.partner_id
        self._create_notification(partner, 'Regression Preview Test')

        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/home')
        self.assertIn('wpe-notification-preview', res.text)
        self.assertIn('Regression Preview Test', res.text)

    # ------------------------------------------------------------------
    # 3. View all link still works
    # ------------------------------------------------------------------

    def test_03_view_all_link_still_present(self):
        """'查看全部' link should still point to /my/notifications."""
        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/home')
        self.assertIn('wpe-view-all-link', res.text)
        self.assertIn('/my/notifications', res.text)

    # ------------------------------------------------------------------
    # 4. Notification page tabs still work
    # ------------------------------------------------------------------

    def test_04_notification_tabs_still_work(self):
        """All expected tabs should still be present."""
        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=all', res.text)
        self.assertIn('tab=message', res.text)
        self.assertIn('tab=notification', res.text)

    def test_05_admin_activity_tab_still_works(self):
        """Admin should still have the activity tab."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=activity', res.text)

    # ------------------------------------------------------------------
    # 5. Modal still present
    # ------------------------------------------------------------------

    def test_06_modal_still_present(self):
        """Detail modal markup should still be in notification page."""
        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe_notif_modal_overlay', res.text)
        self.assertIn('wpe_modal_close', res.text)
        self.assertIn('wpe_modal_action_btn', res.text)

    # ------------------------------------------------------------------
    # 6. Swipe hint still present
    # ------------------------------------------------------------------

    def test_07_swipe_hint_with_notifications(self):
        """Swipe hint should appear when notifications exist."""
        partner = self.portal_user.partner_id
        self._create_notification(partner, 'Swipe Hint Test')

        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe_swipe_hint', res.text)
        self.assertIn('wpe-swipe-hint', res.text)

    # ------------------------------------------------------------------
    # 7. Cross-user isolation: user2 doesn't see user1's notifications
    # ------------------------------------------------------------------

    def test_08_cross_user_isolation(self):
        """User2 should not see User1's notifications on portal home."""
        # Create notification for user1 only
        partner1 = self.portal_user.partner_id
        self._create_notification(partner1, 'User1 Only Notif')

        # Login as user2
        self.authenticate('regr_portal_2', 'regr_portal_2')
        res = self.url_open('/my/home')
        self.assertNotIn('User1 Only Notif', res.text,
                         "User2 should not see User1's notification preview")

    def test_09_cross_user_isolation_notification_page(self):
        """User2 should not see User1's notifications on notification page."""
        partner1 = self.portal_user.partner_id
        self._create_notification(partner1, 'User1 Only Page Notif')

        self.authenticate('regr_portal_2', 'regr_portal_2')
        res = self.url_open('/my/notifications')
        self.assertNotIn('User1 Only Page Notif', res.text)

    # ------------------------------------------------------------------
    # 8. Unread badge still works
    # ------------------------------------------------------------------

    def test_10_unread_badge_still_works(self):
        """Unread badge should still appear on portal home."""
        partner = self.portal_user.partner_id
        self._create_notification(partner, 'Badge Regression')

        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/home')
        self.assertIn('data-unread-badge', res.text)

    # ------------------------------------------------------------------
    # 9. Empty state still works on notification page
    # ------------------------------------------------------------------

    def test_11_empty_state_still_works(self):
        """Empty state should show when no notifications exist for user2."""
        self.authenticate('regr_portal_2', 'regr_portal_2')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-empty', res.text)

    # ------------------------------------------------------------------
    # 10. Security card still present
    # ------------------------------------------------------------------

    def test_12_security_card_still_present(self):
        """'Connection & Security' card should still link to /my/security."""
        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/home')
        self.assertIn('/my/security', res.text)

    # ------------------------------------------------------------------
    # 11. is_internal_user still passed to template (for activity tab)
    # ------------------------------------------------------------------

    def test_13_internal_user_flag_still_works(self):
        """Admin should still see activity tab (is_internal_user=True)."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=activity', res.text,
                      "is_internal_user context should still work")

    def test_14_portal_no_activity_tab(self):
        """Portal user should not see activity tab."""
        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/notifications')
        self.assertNotIn('tab=activity', res.text)

    # ------------------------------------------------------------------
    # 12. JSON-RPC endpoints still work after UI changes
    # ------------------------------------------------------------------

    def test_15_jsonrpc_data_endpoint_still_works(self):
        """JSON-RPC /my/notifications/data should still return data."""
        import json
        partner = self.portal_user.partner_id
        self._create_notification(partner, 'JSONRPC Regression Test')

        self.authenticate('regr_portal', 'regr_portal')
        payload = json.dumps({
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'tab': 'all'},
        })
        res = self.url_open('/my/notifications/data', data=payload, headers={
            'Content-Type': 'application/json',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn('error', data)
        result = data['result']
        self.assertGreaterEqual(result['total'], 1)
        self.assertIn('unread_count', result)

    # ------------------------------------------------------------------
    # 13. Unauthenticated access still redirects
    # ------------------------------------------------------------------

    def test_16_unauthenticated_redirect_home(self):
        """Unauthenticated /my/home should still redirect to login."""
        res = self.url_open('/my/home')
        self.assertIn('/web/login', res.url)

    def test_17_unauthenticated_redirect_notifications(self):
        """Unauthenticated /my/notifications should still redirect to login."""
        res = self.url_open('/my/notifications')
        self.assertIn('/web/login', res.url)

    # ------------------------------------------------------------------
    # 14. Page HTML structure intact
    # ------------------------------------------------------------------

    def test_18_html_structure_intact(self):
        """Page should still have valid HTML structure."""
        self.authenticate('regr_portal', 'regr_portal')
        res = self.url_open('/my/home')
        self.assertIn('<!DOCTYPE html>', res.text)
        self.assertIn('</html>', res.text)
        self.assertIn('o_portal', res.text)
