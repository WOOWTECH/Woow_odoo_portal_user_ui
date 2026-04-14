# -*- coding: utf-8 -*-
"""
Unit tests for WoowPortalEnhanced controller.

Covers:
  - Portal home route (/my, /my/home)
  - _prepare_home_portal_values
  - Notification preview on home page
  - /my/notifications HTTP page
  - /my/notifications/data JSON-RPC endpoint
  - Tab filtering, pagination, edge cases
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
        """When no activities, empty state message should appear."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        # The Chinese empty state text
        self.assertIn('fa-check-circle', res.text,
                      "Empty notification state should show check-circle icon")

    # ------------------------------------------------------------------
    # 4. Notification preview with activities
    # ------------------------------------------------------------------

    def test_08_notification_preview_with_activities(self):
        """When activities exist, they should appear in the preview."""
        # Create an activity for admin
        partner = self.env.ref('base.partner_admin')
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': partner.id,
            'user_id': self.admin_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Test WPE Activity',
            'date_deadline': fields.Date.today(),
        })

        self.authenticate('admin', 'admin')
        res = self.url_open('/my/home')
        self.assertIn('Test WPE Activity', res.text,
                      "Activity summary should appear in the notification preview")

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
        """Notification drawer should NOT be in the page (removed in refactor)."""
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
        """Notification page should have tab links."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertIn('tab=all', res.text)
        self.assertIn('tab=todo', res.text)
        self.assertIn('tab=system', res.text)

    def test_16_notification_page_redirects_unauthenticated(self):
        """Unauthenticated users should be redirected from notifications."""
        res = self.url_open('/my/notifications')
        self.assertIn('/web/login', res.url)

    def test_17_notification_page_with_activities(self):
        """Notification page should show activity cards."""
        partner = self.admin_user.partner_id
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': partner.id,
            'user_id': self.admin_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Notif Page Test',
            'date_deadline': fields.Date.today(),
        })

        self.authenticate('admin', 'admin')
        res = self.url_open('/my/notifications')
        self.assertIn('Notif Page Test', res.text)
        self.assertIn('wpe-notif-card-wrapper', res.text)

    def test_18_notification_page_empty_state(self):
        """When no activities, notification page should show empty state."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/notifications')
        self.assertIn('wpe-notif-empty', res.text)

    def test_19_notification_page_view_all_link(self):
        """Home page should have a link to /my/notifications."""
        self.authenticate('test_portal_wpe', 'test_portal_wpe')
        res = self.url_open('/my/home')
        self.assertIn('/my/notifications', res.text)
        self.assertIn('wpe-view-all-link', res.text)


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

        # Create activities for the portal user
        partner = cls.portal_user.partner_id
        model_id = cls.env['ir.model']._get('res.partner').id
        todo_type = cls.env.ref('mail.mail_activity_data_todo')

        for i in range(5):
            cls.env['mail.activity'].sudo().create({
                'res_model_id': model_id,
                'res_id': partner.id,
                'user_id': cls.portal_user.id,
                'activity_type_id': todo_type.id,
                'summary': 'Notif Test %d' % (i + 1),
                'date_deadline': fields.Date.today() + timedelta(days=i),
            })

        # Create activities for admin (should NOT be visible to portal user)
        admin_partner = cls.env.ref('base.partner_admin')
        for i in range(3):
            cls.env['mail.activity'].sudo().create({
                'res_model_id': model_id,
                'res_id': admin_partner.id,
                'user_id': cls.admin_user.id,
                'activity_type_id': todo_type.id,
                'summary': 'Admin Activity %d' % (i + 1),
                'date_deadline': fields.Date.today(),
            })

    # ------------------------------------------------------------------
    # 1. Basic fetch
    # ------------------------------------------------------------------

    def test_01_fetch_all_notifications(self):
        """Fetch all notifications for a portal user."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {'tab': 'all'})
        self.assertEqual(result['total'], 5)
        self.assertEqual(len(result['activities']), 5)

    # ------------------------------------------------------------------
    # 2. Cross-user isolation
    # ------------------------------------------------------------------

    def test_02_cross_user_isolation(self):
        """Portal user should NOT see admin's activities."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {'tab': 'all'})
        summaries = [a['summary'] for a in result['activities']]
        for s in summaries:
            self.assertNotIn('Admin Activity', s,
                             "Portal user should not see admin activities")

    def test_03_admin_sees_own_activities(self):
        """Admin should see own activities, not portal user's."""
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request('/my/notifications/data', {'tab': 'all'})
        summaries = [a['summary'] for a in result['activities']]
        for s in summaries:
            self.assertNotIn('Notif Test', s,
                             "Admin should not see portal user's activities")
        # Admin should see at least their 3 test activities
        self.assertGreaterEqual(result['total'], 3)

    # ------------------------------------------------------------------
    # 3. Pagination
    # ------------------------------------------------------------------

    def test_04_pagination_limit(self):
        """Limit parameter should cap the number of returned activities."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 2,
        })
        self.assertEqual(len(result['activities']), 2)
        self.assertEqual(result['total'], 5)  # total is still 5

    def test_05_pagination_offset(self):
        """Offset should skip records."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 2, 'offset': 3,
        })
        self.assertEqual(len(result['activities']), 2)  # 5 - 3 = 2 remaining
        self.assertEqual(result['total'], 5)

    def test_06_pagination_beyond_total(self):
        """Offset beyond total should return empty."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 10, 'offset': 100,
        })
        self.assertEqual(len(result['activities']), 0)
        self.assertEqual(result['total'], 5)

    # ------------------------------------------------------------------
    # 4. limit=0 edge case (badge count only)
    # ------------------------------------------------------------------

    def test_07_limit_zero_returns_count_only(self):
        """limit=0 should return empty activities but correct total."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 0,
        })
        self.assertEqual(len(result['activities']), 0)
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
        # Should not crash; returns up to 100 records
        self.assertLessEqual(len(result['activities']), 100)

    def test_09_negative_limit_clamped_to_zero(self):
        """Negative limit should be clamped to 0 (count-only mode)."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': -5,
        })
        self.assertEqual(len(result['activities']), 0)
        self.assertEqual(result['total'], 5)

    # ------------------------------------------------------------------
    # 6. Tab filtering
    # ------------------------------------------------------------------

    def test_10_tab_todo(self):
        """Tab 'todo' should filter by activity_category='default'."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {'tab': 'todo'})
        # All our test activities use mail_activity_data_todo which has category 'default'
        self.assertEqual(result['total'], 5)

    def test_11_tab_system(self):
        """Tab 'system' should filter by activity_category != 'default'."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {'tab': 'system'})
        # None of our test activities are system type
        self.assertEqual(result['total'], 0)

    def test_12_tab_unknown_acts_as_all(self):
        """Unknown tab value should act as 'all' (no extra filter)."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {'tab': 'xyz'})
        self.assertEqual(result['total'], 5)

    # ------------------------------------------------------------------
    # 7. Activity data fields
    # ------------------------------------------------------------------

    def test_13_activity_data_structure(self):
        """Each activity in the response should have all required fields."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 1,
        })
        act = result['activities'][0]
        required_keys = [
            'id', 'summary', 'res_name', 'res_model', 'res_id',
            'activity_type', 'activity_category', 'date_deadline',
            'time_ago', 'can_approve', 'icon',
        ]
        for key in required_keys:
            self.assertIn(key, act, "Activity should have key '%s'" % key)

    def test_14_time_ago_format(self):
        """time_ago should be a non-empty string."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {
            'tab': 'all', 'limit': 1,
        })
        act = result['activities'][0]
        self.assertTrue(act['time_ago'], "time_ago should be a non-empty string")

    # ------------------------------------------------------------------
    # 8. Ordering
    # ------------------------------------------------------------------

    def test_15_ordering_by_deadline(self):
        """Activities should be ordered by date_deadline ascending."""
        self.authenticate('test_portal_notif', 'test_portal_notif')
        result = self.make_jsonrpc_request('/my/notifications/data', {'tab': 'all'})
        deadlines = [a['date_deadline'] for a in result['activities']]
        self.assertEqual(deadlines, sorted(deadlines),
                         "Activities should be ordered by deadline ascending")

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
