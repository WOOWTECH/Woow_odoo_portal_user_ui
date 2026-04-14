# -*- coding: utf-8 -*-
"""
Unit tests for WoowPortalEnhanced controller.

Covers:
  - Portal home route (/my, /my/home)
  - _prepare_home_portal_values
  - Notification preview on home page (mail.notification)
  - /my/notifications HTTP page
  - /my/notifications/data JSON-RPC endpoint
  - Tab filtering (message/notification/activity), pagination, edge cases
"""

from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPortalHome(HttpCase):
    """Test the enhanced portal home page rendering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')
        # Create a portal user
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Test Portal User',
            'login': 'test_portal_wpe',
            'password': 'test_portal_wpe',
            'email': 'portal_wpe@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    @classmethod
    def _create_notification(cls, partner, subject='Test Notification',
                             message_type='notification', is_read=False,
                             body='', author=None):
        """Helper to create a mail.message + mail.notification pair."""
        msg = cls.env['mail.message'].sudo().create({
            'model': 'res.partner',
            'res_id': partner.id,
            'subject': subject,
            'body': body or '<p>%s</p>' % subject,
            'message_type': message_type,
            'subtype_id': cls.env.ref('mail.mt_comment').id,
            'author_id': author.id if author else partner.id,
        })
        notif = cls.env['mail.notification'].sudo().create({
            'mail_message_id': msg.id,
            'res_partner_id': partner.id,
            'notification_type': 'inbox',
            'is_read': is_read,
        })
        return notif

    # ------------------------------------------------------------------
    # 1. Route accessibility
    # ------------------------------------------------------------------

    def test_01_portal_home_redirects_unauthenticated(self):
        """Unauthenticated users are redirected to login."""
        res = self.url_open('/my/home')
        self.assertIn('/web/login', res.url,
                      "Unauthenticated access to /my/home should redirect to login")

    def test_02_portal_home_accessible_for_portal_user(self):
        """Portal users can access the enhanced home page."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertEqual(res.status_code, 200)
        self.assertIn('wpe-search-bar', res.text,
                      "Enhanced portal home should contain the search bar")

    def test_03_portal_home_accessible_for_admin(self):
        """Admin users can access the enhanced home page."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertEqual(res.status_code, 200)
        self.assertIn('wpe-admin-banner', res.text,
                      "Admin should see the admin banner on portal home")

    def test_04_portal_home_no_admin_banner_for_portal_user(self):
        """Portal users should NOT see the admin banner."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe-admin-banner', res.text,
                         "Portal user should not see the admin banner")

    def test_05_portal_my_route_also_works(self):
        """/my route should also render the enhanced home."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my')
        self.assertEqual(res.status_code, 200)
        self.assertIn('wpe-search-bar', res.text)

    # ------------------------------------------------------------------
    # 2. Search bar presence
    # ------------------------------------------------------------------

    def test_06_search_bar_present(self):
        """Search bar input should be present in the rendered page."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertIn('wpe_module_search', res.text)

    # ------------------------------------------------------------------
    # 3. Notification preview (empty state)
    # ------------------------------------------------------------------

    def test_07_notification_preview_empty_state(self):
        """When no notifications, empty state message should appear."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        # The Chinese empty state text
        self.assertIn('fa-check-circle', res.text,
                      "Empty notification state should show check-circle icon")

    # ------------------------------------------------------------------
    # 4. Notification preview with mail.notification
    # ------------------------------------------------------------------

    def test_08_notification_preview_with_notifications(self):
        """When mail.notifications exist, they should appear in preview."""
        partner = self.portal_user.partner_id
        self._create_notification(
            partner, subject='Test WPE Notification',
            message_type='notification', is_read=False)

        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertIn('Test WPE Notification', res.text,
                      "Notification subject should appear in the preview")

    def test_08b_notification_preview_shows_unread_badge(self):
        """Unread badge should show on portal home when unread exist."""
        partner = self.portal_user.partner_id
        self._create_notification(
            partner, subject='Badge Test', is_read=False)

        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertIn('data-unread-badge', res.text,
                      "Unread badge should be present when unread exist")

    # ------------------------------------------------------------------
    # 5. Module grid presence
    # ------------------------------------------------------------------

    def test_09_module_grid_present(self):
        """Module grid section should be present with correct id."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertIn('wpe_module_grid', res.text)
        self.assertIn('o_portal_docs', res.text)

    # ------------------------------------------------------------------
    # 6. No bell icon (removed)
    # ------------------------------------------------------------------

    def test_10_no_bell_icon(self):
        """Bell icon should NOT be in the page (removed in refactor)."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe_bell_trigger', res.text)
        self.assertNotIn('wpe_bell_badge', res.text)

    # ------------------------------------------------------------------
    # 7. No drawer (removed)
    # ------------------------------------------------------------------

    def test_11_no_drawer(self):
        """Notification drawer should NOT be in the page (removed)."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe_drawer', res.text)
        self.assertNotIn('wpe_drawer_backdrop', res.text)

    # ------------------------------------------------------------------
    # 8. Return to Backend link (admin only)
    # ------------------------------------------------------------------

    def test_12_return_backend_link_for_admin(self):
        """Admin should see 'Return to Backend' in dropdown."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertIn('wpe_return_backend_link', res.text)

    def test_13_no_return_backend_link_for_portal(self):
        """Portal user should NOT see 'Return to Backend'."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertNotIn('wpe_return_backend_link', res.text)

    # ------------------------------------------------------------------
    # 9. Notification page (HTTP GET /my/notifications)
    # ------------------------------------------------------------------

    def test_14_notification_page_accessible(self):
        """Portal user can access the notification list page."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertEqual(res.status_code, 200)
        self.assertIn('wpe-notif-tabs', res.text)

    def test_15_notification_page_has_tabs(self):
        """Notification page should have the correct tab links."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=all', res.text)
        self.assertIn('tab=message', res.text)
        self.assertIn('tab=notification', res.text)

    def test_15b_notification_page_portal_no_activity_tab(self):
        """Portal user should NOT see the activity tab."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertNotIn('tab=activity', res.text,
                         "Portal user should not see the activity tab")

    def test_15c_notification_page_admin_has_activity_tab(self):
        """Admin (internal) user should see the activity tab."""
        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=activity', res.text,
                      "Internal user should see the activity tab")

    def test_16_notification_page_redirects_unauthenticated(self):
        """Unauthenticated users should be redirected from notifications."""
        res = self.url_open('/my/notifications')
        self.assertIn('/web/login', res.url)

    def test_17_notification_page_with_notifications(self):
        """Notification page should show notification cards."""
        partner = self.portal_user.partner_id
        self._create_notification(
            partner, subject='Notif Page Test',
            message_type='notification', is_read=False)

        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertIn('Notif Page Test', res.text)
        self.assertIn('wpe-notif-card-wrapper', res.text)
        self.assertIn('data-notif-id', res.text,
                      "Notification cards should have data-notif-id")

    def test_17b_notification_page_with_activities_admin(self):
        """Activity cards should show for admin users."""
        partner = self.admin_user.partner_id
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': partner.id,
            'user_id': self.admin_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Admin Activity Test',
            'date_deadline': fields.Date.today(),
        })

        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications?tab=activity')
        self.assertIn('Admin Activity Test', res.text)
        self.assertIn('data-activity-id', res.text,
                      "Activity cards should have data-activity-id")

    def test_18_notification_page_empty_state(self):
        """When no notifications, page should show empty state."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-empty', res.text)

    def test_19_notification_page_view_all_link(self):
        """Home page should have a link to /my/notifications."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertIn('/my/notifications', res.text)
        self.assertIn('wpe-view-all-link', res.text)

    def test_20_notification_page_has_modal(self):
        """Notification page should include the detail modal markup."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe_notif_modal_overlay', res.text,
                      "Modal overlay should be present")
        self.assertIn('wpe_notif_modal', res.text,
                      "Modal container should be present")
        self.assertIn('wpe_modal_close', res.text,
                      "Modal close button should be present")


@tagged('post_install', '-at_install')
class TestNotificationEndpoint(HttpCase):
    """Test the /my/notifications/data JSON-RPC endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Test Portal Notif',
            'login': 'test_portal_notif',
            'password': 'test_portal_notif',
            'email': 'portal_notif@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.portal_partner = cls.portal_user.partner_id
        cls.admin_partner = cls.admin_user.partner_id

        # Create 3 comment-type notifications for portal user
        for i in range(3):
            cls._create_notification(
                cls.portal_partner,
                subject='Comment %d' % (i + 1),
                message_type='comment',
                is_read=False,
            )

        # Create 2 system-type notifications for portal user
        for i in range(2):
            cls._create_notification(
                cls.portal_partner,
                subject='SysNotif %d' % (i + 1),
                message_type='notification',
                is_read=False,
            )

        # Create notifications for admin (should NOT be visible to portal)
        for i in range(3):
            cls._create_notification(
                cls.admin_partner,
                subject='Admin Notif %d' % (i + 1),
                message_type='notification',
                is_read=False,
            )

        # Create activities for admin (only visible in activity tab)
        model_id = cls.env['ir.model']._get('res.partner').id
        todo_type = cls.env.ref('mail.mail_activity_data_todo')
        for i in range(2):
            cls.env['mail.activity'].sudo().create({
                'res_model_id': model_id,
                'res_id': cls.admin_partner.id,
                'user_id': cls.admin_user.id,
                'activity_type_id': todo_type.id,
                'summary': 'Admin Activity %d' % (i + 1),
                'date_deadline': fields.Date.today() + timedelta(days=i),
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

    # ------------------------------------------------------------------
    # 1. Basic fetch
    # ------------------------------------------------------------------

    def test_01_fetch_all_notifications(self):
        """Fetch all notifications for a portal user."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'all'})
        # Portal user has 5 notifications (3 comment + 2 system), no activities
        self.assertEqual(result['total'], 5)
        self.assertEqual(len(result['notifications']), 5)

    # ------------------------------------------------------------------
    # 2. Cross-user isolation
    # ------------------------------------------------------------------

    def test_02_cross_user_isolation(self):
        """Portal user should NOT see admin's notifications."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'all'})
        subjects = [n['subject'] for n in result['notifications']]
        for s in subjects:
            self.assertNotIn('Admin', s,
                             "Portal user should not see admin notifications")

    def test_03_admin_sees_own_notifications(self):
        """Admin should see own notifications, not portal user's."""
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'all'})
        subjects = [n.get('subject', '') for n in result['notifications']]
        for s in subjects:
            self.assertNotIn('Comment', s,
                             "Admin should not see portal user's comments")

    # ------------------------------------------------------------------
    # 3. Pagination
    # ------------------------------------------------------------------

    def test_04_pagination_limit(self):
        """Limit parameter should cap the number of returned items."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 2,
        })
        self.assertEqual(len(result['notifications']), 2)
        self.assertEqual(result['total'], 5)

    def test_05_pagination_offset(self):
        """Offset should skip records."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 2, 'offset': 3,
        })
        self.assertEqual(len(result['notifications']), 2)  # 5 - 3 = 2
        self.assertEqual(result['total'], 5)

    def test_06_pagination_beyond_total(self):
        """Offset beyond total should return empty."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 10, 'offset': 100,
        })
        self.assertEqual(len(result['notifications']), 0)
        self.assertEqual(result['total'], 5)

    # ------------------------------------------------------------------
    # 4. limit=0 edge case (count only)
    # ------------------------------------------------------------------

    def test_07_limit_zero_returns_count_only(self):
        """limit=0 should return empty list but correct total."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 0,
        })
        self.assertEqual(len(result['notifications']), 0)
        self.assertEqual(result['total'], 5)

    # ------------------------------------------------------------------
    # 5. Limit clamping
    # ------------------------------------------------------------------

    def test_08_limit_clamped_to_max(self):
        """Limit above _MAX_LIMIT should be clamped."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 99999,
        })
        self.assertLessEqual(len(result['notifications']), 100)

    def test_09_negative_limit_clamped_to_zero(self):
        """Negative limit should be clamped to 0 (count-only mode)."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': -5,
        })
        self.assertEqual(len(result['notifications']), 0)
        self.assertEqual(result['total'], 5)

    # ------------------------------------------------------------------
    # 6. Tab filtering
    # ------------------------------------------------------------------

    def test_10_tab_message(self):
        """Tab 'message' should return only comment/email type."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'message'})
        self.assertEqual(result['total'], 3,
                         "Should have 3 comment-type notifications")
        for n in result['notifications']:
            self.assertIn(n['message_type'], ('comment', 'email'))

    def test_11_tab_notification(self):
        """Tab 'notification' should return system notification types."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'notification'})
        self.assertEqual(result['total'], 2,
                         "Should have 2 system-type notifications")
        for n in result['notifications']:
            self.assertIn(n['message_type'],
                          ('notification', 'auto_comment', 'user_notification'))

    def test_12_tab_activity_portal_user_gets_zero(self):
        """Portal user requesting activity tab should get 0."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'activity'})
        self.assertEqual(result['total'], 0,
                         "Portal user should have no activities")

    def test_12b_tab_activity_admin_gets_activities(self):
        """Admin requesting activity tab should get activity items."""
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'activity'})
        self.assertGreaterEqual(result['total'], 2)
        # Activity items should have activity_id, not notif_id
        for item in result['notifications']:
            self.assertIn('activity_id', item)

    def test_13_tab_unknown_acts_as_all(self):
        """Unknown tab value should act as 'all'."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'xyz'})
        self.assertEqual(result['total'], 5)

    # ------------------------------------------------------------------
    # 7. Notification data fields
    # ------------------------------------------------------------------

    def test_14_notification_data_structure(self):
        """Each notification should have all required fields."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'message', 'limit': 1,
        })
        notif = result['notifications'][0]
        required_keys = [
            'notif_id', 'message_id', 'subject', 'body_preview',
            'record_name', 'model', 'res_id', 'author_name',
            'date', 'time_ago', 'is_read', 'icon', 'document_url',
            'message_type',
        ]
        for key in required_keys:
            self.assertIn(key, notif,
                          "Notification should have key '%s'" % key)

    def test_14b_activity_data_structure(self):
        """Each activity should have all required fields."""
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'activity', 'limit': 1,
        })
        act = result['notifications'][0]
        required_keys = [
            'activity_id', 'summary', 'res_name', 'res_model', 'res_id',
            'activity_type', 'activity_category', 'date_deadline',
            'time_ago', 'can_approve', 'icon', 'document_url',
        ]
        for key in required_keys:
            self.assertIn(key, act, "Activity should have key '%s'" % key)

    def test_15_time_ago_format(self):
        """time_ago should be a non-empty string."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 1,
        })
        notif = result['notifications'][0]
        self.assertTrue(notif['time_ago'],
                        "time_ago should be a non-empty string")

    # ------------------------------------------------------------------
    # 8. Unread count
    # ------------------------------------------------------------------

    def test_16_unread_count(self):
        """Response should include unread_count."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request(
            '/my/notifications/data', {'tab': 'all'})
        self.assertIn('unread_count', result)
        self.assertGreaterEqual(result['unread_count'], 5,
                                "Should have at least 5 unread notifications")

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def make_jsonrpc_request(self, url, params=None):
        """Send a JSON-RPC request and return the result."""
        import json
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': params or {},
        })
        res = self.url_open(url, data=payload, headers={
            'Content-Type': 'application/json',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn('error', data,
                         "JSON-RPC should not return an error: %s" % data.get('error'))
        return data['result']
