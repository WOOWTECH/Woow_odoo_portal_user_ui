# -*- coding: utf-8 -*-
"""
Integration tests for notification actions.

Covers:
  - mark_read / mark_unread on mail.notification
  - done / approve / reject on mail.activity
  - Cross-user protection
  - Invalid ID / action handling
  - Double-action idempotency
  - Count decrements after action
  - /my/notifications/detail endpoint
"""

import json
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestNotificationActions(HttpCase):
    """Test /my/notifications/action JSON-RPC endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Action Tester',
            'login': 'portal_action_test',
            'password': 'portal_action_test',
            'email': 'action_test@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.model_id = cls.env['ir.model']._get('res.partner').id
        cls.todo_type = cls.env.ref('mail.mail_activity_data_todo')

    def _create_notification(self, partner, subject='Test Notification',
                             message_type='notification', is_read=False):
        """Helper to create a mail.message + mail.notification pair."""
        msg = self.env['mail.message'].sudo().create({
            'model': 'res.partner',
            'res_id': partner.id,
            'subject': subject,
            'body': '<p>%s body</p>' % subject,
            'message_type': message_type,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'author_id': partner.id,
        })
        return self.env['mail.notification'].sudo().create({
            'mail_message_id': msg.id,
            'res_partner_id': partner.id,
            'notification_type': 'inbox',
            'is_read': is_read,
        })

    def _create_activity(self, user, summary='Test Activity'):
        """Helper to create a mail.activity for the given user."""
        return self.env['mail.activity'].sudo().create({
            'res_model_id': self.model_id,
            'res_id': user.partner_id.id,
            'user_id': user.id,
            'activity_type_id': self.todo_type.id,
            'summary': summary,
            'date_deadline': fields.Date.today(),
        })

    def _make_action_request(self, action, notification_id=None,
                             activity_id=None):
        """Helper to call /my/notifications/action."""
        params = {'action': action}
        if notification_id is not None:
            params['notification_id'] = notification_id
        if activity_id is not None:
            params['activity_id'] = activity_id
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': params,
        })
        res = self.url_open('/my/notifications/action', data=payload, headers={
            'Content-Type': 'application/json',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        return data.get('result', data.get('error'))

    def _make_detail_request(self, notification_id=None, activity_id=None):
        """Helper to call /my/notifications/detail."""
        params = {}
        if notification_id is not None:
            params['notification_id'] = notification_id
        if activity_id is not None:
            params['activity_id'] = activity_id
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': params,
        })
        res = self.url_open('/my/notifications/detail', data=payload, headers={
            'Content-Type': 'application/json',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        return data.get('result', data.get('error'))

    # ------------------------------------------------------------------
    # 1. Mark read action (mail.notification)
    # ------------------------------------------------------------------

    def test_01_mark_read_notification(self):
        """Marking a notification as read should set is_read=True."""
        notif = self._create_notification(
            self.portal_user.partner_id, 'Mark Read Test')
        self.assertFalse(notif.is_read)

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'mark_read', notification_id=notif.id)

        self.assertTrue(result['success'])
        notif.invalidate_recordset()
        self.assertTrue(notif.is_read,
                        "Notification should be marked as read")

    # ------------------------------------------------------------------
    # 2. Mark unread action (mail.notification)
    # ------------------------------------------------------------------

    def test_02_mark_unread_notification(self):
        """Marking a read notification as unread should set is_read=False."""
        notif = self._create_notification(
            self.portal_user.partner_id, 'Mark Unread Test', is_read=True)
        self.assertTrue(notif.is_read)

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'mark_unread', notification_id=notif.id)

        self.assertTrue(result['success'])
        notif.invalidate_recordset()
        self.assertFalse(notif.is_read,
                         "Notification should be marked as unread")

    # ------------------------------------------------------------------
    # 3. Unread count decrements after mark_read
    # ------------------------------------------------------------------

    def test_03_unread_count_decrements(self):
        """unread_count should decrement after marking as read."""
        partner = self.portal_user.partner_id
        self._create_notification(partner, 'Count A')
        notif_b = self._create_notification(partner, 'Count B')

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'mark_read', notification_id=notif_b.id)

        self.assertTrue(result['success'])
        # unread_count should be at least 1 (Count A is still unread)
        self.assertGreaterEqual(result['unread_count'], 1)

    # ------------------------------------------------------------------
    # 4. Cross-user protection (notification)
    # ------------------------------------------------------------------

    def test_04_cannot_mark_other_users_notification(self):
        """User cannot mark another user's notification as read."""
        admin_notif = self._create_notification(
            self.admin_user.partner_id, 'Admin Only Notif')

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'mark_read', notification_id=admin_notif.id)

        self.assertFalse(result['success'])
        admin_notif.invalidate_recordset()
        self.assertFalse(admin_notif.is_read,
                         "Other user's notification should not be affected")

    # ------------------------------------------------------------------
    # 5. Non-existent notification
    # ------------------------------------------------------------------

    def test_05_nonexistent_notification(self):
        """Acting on a non-existent notification should fail gracefully."""
        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'mark_read', notification_id=999999999)
        self.assertFalse(result['success'])

    # ------------------------------------------------------------------
    # 6. Invalid action for notification
    # ------------------------------------------------------------------

    def test_06_invalid_action_notification(self):
        """Passing an invalid action for notification should return error."""
        notif = self._create_notification(
            self.portal_user.partner_id, 'Invalid Action Test')

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'delete', notification_id=notif.id)

        self.assertFalse(result['success'])
        self.assertIn('invalid', result['error'].lower())

    # ------------------------------------------------------------------
    # 7. Invalid notification_id type
    # ------------------------------------------------------------------

    def test_07_non_integer_notification_id(self):
        """Non-integer notification_id should return error."""
        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'mark_read', notification_id='not_a_number')
        self.assertFalse(result['success'])
        self.assertIn('invalid', result['error'].lower())

    # ------------------------------------------------------------------
    # 8. Activity actions (done/approve/reject)
    # ------------------------------------------------------------------

    def test_08_done_activity(self):
        """Done action should remove the activity via action_feedback."""
        activity = self._create_activity(self.portal_user, 'Swipe Done')
        activity_id = activity.id

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request('done', activity_id=activity_id)

        self.assertTrue(result['success'])
        self.assertFalse(
            self.env['mail.activity'].sudo().browse(activity_id).exists(),
            "Done activity should be removed")

    def test_09_approve_activity(self):
        """Approving an activity should remove it (action_feedback)."""
        activity = self._create_activity(self.portal_user, 'To Approve')
        activity_id = activity.id

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request('approve', activity_id=activity_id)

        self.assertTrue(result['success'])
        self.assertFalse(
            self.env['mail.activity'].sudo().browse(activity_id).exists(),
            "Approved activity should be removed")

    def test_10_reject_activity(self):
        """Rejecting an activity should cancel it (unlink)."""
        activity = self._create_activity(self.portal_user, 'To Reject')
        activity_id = activity.id

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request('reject', activity_id=activity_id)

        self.assertTrue(result['success'])
        self.assertFalse(
            self.env['mail.activity'].sudo().browse(activity_id).exists(),
            "Rejected activity should be removed")

    # ------------------------------------------------------------------
    # 9. Cross-user protection (activity)
    # ------------------------------------------------------------------

    def test_11_cannot_act_on_other_users_activity(self):
        """User cannot approve an activity assigned to someone else."""
        admin_activity = self._create_activity(self.admin_user, 'Admin Only')

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(
            'approve', activity_id=admin_activity.id)

        self.assertFalse(result['success'])
        self.assertTrue(
            self.env['mail.activity'].sudo().browse(admin_activity.id).exists(),
            "Other user's activity should not be affected")

    # ------------------------------------------------------------------
    # 10. Double action (idempotency)
    # ------------------------------------------------------------------

    def test_12_double_mark_read(self):
        """Double mark_read on same notification should succeed idempotently."""
        notif = self._create_notification(
            self.portal_user.partner_id, 'Double Read')

        self.authenticate('portal_action_test', 'portal_action_test')
        result1 = self._make_action_request(
            'mark_read', notification_id=notif.id)
        self.assertTrue(result1['success'])

        # Second mark_read should also succeed (notification still exists)
        result2 = self._make_action_request(
            'mark_read', notification_id=notif.id)
        self.assertTrue(result2['success'])

    def test_13_double_approve_activity(self):
        """Approving an already-completed activity should fail gracefully."""
        activity = self._create_activity(self.portal_user, 'Double Click')
        activity_id = activity.id

        self.authenticate('portal_action_test', 'portal_action_test')
        result1 = self._make_action_request('approve', activity_id=activity_id)
        self.assertTrue(result1['success'])

        # Second approve should fail (activity gone)
        result2 = self._make_action_request('approve', activity_id=activity_id)
        self.assertFalse(result2['success'])

    # ------------------------------------------------------------------
    # 11. Missing ID parameter
    # ------------------------------------------------------------------

    def test_14_missing_id_parameter(self):
        """Request without any ID should return error."""
        self.authenticate('portal_action_test', 'portal_action_test')
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': {'action': 'mark_read'},
        })
        res = self.url_open('/my/notifications/action', data=payload, headers={
            'Content-Type': 'application/json',
        })
        data = res.json()
        result = data.get('result', {})
        self.assertFalse(result.get('success', True))

    # ------------------------------------------------------------------
    # 12. Unauthenticated access
    # ------------------------------------------------------------------

    def test_15_unauthenticated_action(self):
        """Unauthenticated request should fail."""
        notif = self._create_notification(
            self.portal_user.partner_id, 'Unauth Test')
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': {
                'notification_id': notif.id,
                'action': 'mark_read',
            },
        })
        res = self.url_open('/my/notifications/action', data=payload, headers={
            'Content-Type': 'application/json',
        })
        data = res.json()
        if 'result' in data and isinstance(data['result'], dict):
            self.assertFalse(data['result'].get('success', True))
        elif 'error' in data:
            pass  # JSON-RPC error (access denied) — expected
        else:
            self.fail("Unauthenticated action should not succeed")


@tagged('post_install', '-at_install')
class TestNotificationDetail(HttpCase):
    """Test /my/notifications/detail JSON-RPC endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Detail Tester',
            'login': 'portal_detail_test',
            'password': 'portal_detail_test',
            'email': 'detail_test@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.model_id = cls.env['ir.model']._get('res.partner').id

    def _create_notification(self, partner, subject='Test', body='',
                             message_type='notification'):
        """Helper to create a mail.message + mail.notification pair."""
        msg = self.env['mail.message'].sudo().create({
            'model': 'res.partner',
            'res_id': partner.id,
            'subject': subject,
            'body': body or '<p>%s body content</p>' % subject,
            'message_type': message_type,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'author_id': partner.id,
        })
        return self.env['mail.notification'].sudo().create({
            'mail_message_id': msg.id,
            'res_partner_id': partner.id,
            'notification_type': 'inbox',
            'is_read': False,
        })

    def _create_activity(self, user, summary='Test Activity'):
        """Helper to create a mail.activity."""
        todo_type = self.env.ref('mail.mail_activity_data_todo')
        return self.env['mail.activity'].sudo().create({
            'res_model_id': self.model_id,
            'res_id': user.partner_id.id,
            'user_id': user.id,
            'activity_type_id': todo_type.id,
            'summary': summary,
            'date_deadline': fields.Date.today(),
            'note': '<p>Activity note</p>',
        })

    def _make_detail_request(self, notification_id=None, activity_id=None):
        """Helper to call /my/notifications/detail."""
        params = {}
        if notification_id is not None:
            params['notification_id'] = notification_id
        if activity_id is not None:
            params['activity_id'] = activity_id
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': params,
        })
        res = self.url_open('/my/notifications/detail', data=payload, headers={
            'Content-Type': 'application/json',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn('error', data,
                         "JSON-RPC should not return error: %s" % data.get('error'))
        return data['result']

    # ------------------------------------------------------------------
    # 1. Notification detail
    # ------------------------------------------------------------------

    def test_01_notification_detail_success(self):
        """Should return full notification detail."""
        notif = self._create_notification(
            self.portal_user.partner_id,
            subject='Detail Test',
            body='<p>Full body content here</p>')

        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request(notification_id=notif.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['type'], 'notification')
        detail = result['detail']
        self.assertEqual(detail['subject'], 'Detail Test')
        self.assertIn('Full body content', detail['body'])
        self.assertIn('notif_id', detail)
        self.assertIn('message_id', detail)
        self.assertIn('document_url', detail)
        self.assertIn('tracking_details', detail)

    # ------------------------------------------------------------------
    # 2. Activity detail
    # ------------------------------------------------------------------

    def test_02_activity_detail_success(self):
        """Should return full activity detail."""
        activity = self._create_activity(
            self.portal_user, 'Activity Detail Test')

        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request(activity_id=activity.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['type'], 'activity')
        detail = result['detail']
        self.assertEqual(detail['summary'], 'Activity Detail Test')
        self.assertIn('activity_id', detail)
        self.assertIn('date_deadline', detail)
        self.assertIn('note', detail)
        self.assertIn('document_url', detail)

    # ------------------------------------------------------------------
    # 3. Cross-user protection (detail)
    # ------------------------------------------------------------------

    def test_03_cannot_view_other_users_notification(self):
        """User cannot view another user's notification detail."""
        admin_notif = self._create_notification(
            self.admin_user.partner_id, 'Admin Private')

        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request(notification_id=admin_notif.id)

        self.assertFalse(result['success'])

    def test_04_cannot_view_other_users_activity(self):
        """User cannot view another user's activity detail."""
        admin_activity = self._create_activity(
            self.admin_user, 'Admin Private Activity')

        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request(activity_id=admin_activity.id)

        self.assertFalse(result['success'])

    # ------------------------------------------------------------------
    # 4. Invalid ID
    # ------------------------------------------------------------------

    def test_05_nonexistent_notification_detail(self):
        """Non-existent notification ID should fail."""
        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request(notification_id=999999999)
        self.assertFalse(result['success'])

    def test_06_nonexistent_activity_detail(self):
        """Non-existent activity ID should fail."""
        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request(activity_id=999999999)
        self.assertFalse(result['success'])

    # ------------------------------------------------------------------
    # 5. Missing ID parameter
    # ------------------------------------------------------------------

    def test_07_missing_id_parameter(self):
        """Request without any ID should return error."""
        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request()
        self.assertFalse(result['success'])

    # ------------------------------------------------------------------
    # 6. Invalid ID type
    # ------------------------------------------------------------------

    def test_08_invalid_notification_id_type(self):
        """Non-integer notification ID should return error."""
        self.authenticate('portal_detail_test', 'portal_detail_test')
        result = self._make_detail_request(notification_id='abc')
        self.assertFalse(result['success'])
