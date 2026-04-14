# -*- coding: utf-8 -*-
"""
Integration tests for notification actions (approve / reject).

Covers:
  - Approve completes the activity (action_feedback)
  - Reject cancels the activity (action_cancel / unlink)
  - Cross-user protection (cannot act on another user's activity)
  - Invalid activity ID handling
  - Invalid action handling
  - Non-integer activity ID handling
  - Double-action idempotency
  - Count decrements after action
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

    def _make_action_request(self, activity_id, action):
        """Helper to call /my/notifications/action."""
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': {
                'activity_id': activity_id,
                'action': action,
            },
        })
        res = self.url_open('/my/notifications/action', data=payload, headers={
            'Content-Type': 'application/json',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        return data.get('result', data.get('error'))

    def _make_notifications_request(self, params=None):
        """Helper to call /my/notifications."""
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': params or {'tab': 'all', 'limit': 0},
        })
        res = self.url_open('/my/notifications', data=payload, headers={
            'Content-Type': 'application/json',
        })
        return res.json()['result']

    # ------------------------------------------------------------------
    # 1. Approve action
    # ------------------------------------------------------------------

    def test_01_approve_completes_activity(self):
        """Approving an activity should remove it (action_feedback)."""
        activity = self._create_activity(self.portal_user, 'To Approve')
        activity_id = activity.id

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(activity_id, 'approve')

        self.assertTrue(result['success'])
        # Activity should no longer exist
        self.assertFalse(
            self.env['mail.activity'].sudo().browse(activity_id).exists(),
            "Approved activity should be removed"
        )

    # ------------------------------------------------------------------
    # 2. Reject action
    # ------------------------------------------------------------------

    def test_02_reject_cancels_activity(self):
        """Rejecting an activity should cancel it (action_cancel / unlink)."""
        activity = self._create_activity(self.portal_user, 'To Reject')
        activity_id = activity.id

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(activity_id, 'reject')

        self.assertTrue(result['success'])
        # Activity should no longer exist (action_cancel unlinks)
        self.assertFalse(
            self.env['mail.activity'].sudo().browse(activity_id).exists(),
            "Rejected activity should be removed"
        )

    # ------------------------------------------------------------------
    # 3. Count decrements after action
    # ------------------------------------------------------------------

    def test_03_count_decrements_after_approve(self):
        """new_count should reflect one less activity after approval."""
        self._create_activity(self.portal_user, 'Activity A')
        act_b = self._create_activity(self.portal_user, 'Activity B')

        self.authenticate('portal_action_test', 'portal_action_test')

        # Before: should have 2
        data = self._make_notifications_request()
        self.assertEqual(data['total'], 2)

        # Approve one
        result = self._make_action_request(act_b.id, 'approve')
        self.assertTrue(result['success'])
        self.assertEqual(result['new_count'], 1,
                         "Count should decrement after action")

    # ------------------------------------------------------------------
    # 4. Cross-user protection
    # ------------------------------------------------------------------

    def test_04_cannot_act_on_other_users_activity(self):
        """User cannot approve/reject an activity assigned to someone else."""
        admin_activity = self._create_activity(self.admin_user, 'Admin Only')

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(admin_activity.id, 'approve')

        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'].lower(),
                       "Should return 'not found' for other user's activity")
        # Activity should still exist
        self.assertTrue(
            self.env['mail.activity'].sudo().browse(admin_activity.id).exists(),
            "Other user's activity should not be affected"
        )

    # ------------------------------------------------------------------
    # 5. Non-existent activity
    # ------------------------------------------------------------------

    def test_05_nonexistent_activity(self):
        """Acting on a non-existent activity ID should fail gracefully."""
        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(999999999, 'approve')

        self.assertFalse(result['success'])

    # ------------------------------------------------------------------
    # 6. Invalid action
    # ------------------------------------------------------------------

    def test_06_invalid_action(self):
        """Passing an invalid action should return an error."""
        activity = self._create_activity(self.portal_user, 'Invalid Action Test')

        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(activity.id, 'delete')

        self.assertFalse(result['success'])
        self.assertIn('invalid', result['error'].lower())
        # Activity should still exist
        self.assertTrue(
            self.env['mail.activity'].sudo().browse(activity.id).exists(),
            "Activity should not be affected by invalid action"
        )

    # ------------------------------------------------------------------
    # 7. Invalid activity_id type
    # ------------------------------------------------------------------

    def test_07_non_integer_activity_id(self):
        """Non-integer activity_id should return an error, not crash."""
        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request('not_a_number', 'approve')

        self.assertFalse(result['success'])
        self.assertIn('invalid', result['error'].lower())

    def test_08_none_activity_id(self):
        """None activity_id should return an error."""
        self.authenticate('portal_action_test', 'portal_action_test')
        result = self._make_action_request(None, 'approve')

        self.assertFalse(result['success'])

    # ------------------------------------------------------------------
    # 8. Double action (idempotency)
    # ------------------------------------------------------------------

    def test_09_double_approve(self):
        """Approving an already-completed activity should fail gracefully."""
        activity = self._create_activity(self.portal_user, 'Double Click')
        activity_id = activity.id

        self.authenticate('portal_action_test', 'portal_action_test')

        # First approve succeeds
        result1 = self._make_action_request(activity_id, 'approve')
        self.assertTrue(result1['success'])

        # Second approve should fail (activity gone)
        result2 = self._make_action_request(activity_id, 'approve')
        self.assertFalse(result2['success'])

    # ------------------------------------------------------------------
    # 9. Unauthenticated access
    # ------------------------------------------------------------------

    def test_10_unauthenticated_action(self):
        """Unauthenticated request to /my/notifications/action should fail."""
        activity = self._create_activity(self.portal_user, 'Unauth Test')
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': {
                'activity_id': activity.id,
                'action': 'approve',
            },
        })
        res = self.url_open('/my/notifications/action', data=payload, headers={
            'Content-Type': 'application/json',
        })
        # Should not succeed — either redirect to login or return error
        data = res.json()
        if 'result' in data and isinstance(data['result'], dict):
            # If it somehow reached our controller, success must be False
            self.assertFalse(data['result'].get('success', True))
        elif 'error' in data:
            # JSON-RPC error (access denied) — expected
            pass
        else:
            self.fail("Unauthenticated action should not succeed")

    # ------------------------------------------------------------------
    # 10. Approve/Reject differentiation
    # ------------------------------------------------------------------

    def test_11_approve_vs_reject_are_different(self):
        """
        Approve uses action_feedback (marks done with message).
        Reject uses action_cancel (unlinks without feedback).
        Both remove the activity, but through different paths.
        """
        act_approve = self._create_activity(self.portal_user, 'Approve Path')
        act_reject = self._create_activity(self.portal_user, 'Reject Path')

        self.authenticate('portal_action_test', 'portal_action_test')

        # Approve
        res1 = self._make_action_request(act_approve.id, 'approve')
        self.assertTrue(res1['success'])

        # Reject
        res2 = self._make_action_request(act_reject.id, 'reject')
        self.assertTrue(res2['success'])

        # Both should be gone
        self.assertFalse(
            self.env['mail.activity'].sudo().browse(act_approve.id).exists())
        self.assertFalse(
            self.env['mail.activity'].sudo().browse(act_reject.id).exists())
