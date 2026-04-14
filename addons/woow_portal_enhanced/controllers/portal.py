# -*- coding: utf-8 -*-

import json
from datetime import datetime

from odoo import _, http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class WoowPortalEnhanced(CustomerPortal):

    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kw):
        """Override portal home to inject enhanced data."""
        values = self._prepare_home_portal_values(counters=None)
        values.update(self._prepare_enhanced_home_values())
        return request.render('woow_portal_enhanced.portal_my_home_enhanced', values)

    def _prepare_enhanced_home_values(self):
        """Prepare additional values for the enhanced portal home."""
        user = request.env.user
        is_internal = user._is_internal()

        # Fetch recent activities (notifications)
        activities = self._get_user_activities(limit=3)

        # Activity count for badge
        activity_count = request.env['mail.activity'].sudo().search_count([
            ('user_id', '=', user.id),
        ])

        return {
            'activities': activities,
            'activity_count': activity_count,
            'is_internal_user': is_internal,
        }

    def _get_user_activities(self, limit=20):
        """Fetch mail.activity records for the current user."""
        user = request.env.user
        Activity = request.env['mail.activity'].sudo()
        activities = Activity.search(
            [('user_id', '=', user.id)],
            order='date_deadline asc, id desc',
            limit=limit,
        )
        return activities

    # ------------------------------------------------------------------
    # JSON-RPC endpoints for notification drawer
    # ------------------------------------------------------------------

    @http.route('/my/notifications', type='json', auth='user', methods=['POST'])
    def get_notifications(self, tab='all', limit=20, offset=0, **kw):
        """Return activity list for the notification drawer."""
        user = request.env.user
        domain = [('user_id', '=', user.id)]

        if tab == 'todo':
            domain.append(('activity_category', '=', 'default'))
        elif tab == 'system':
            domain.append(('activity_category', '!=', 'default'))

        Activity = request.env['mail.activity'].sudo()
        total = Activity.search_count(domain)
        activities = Activity.search(
            domain,
            order='date_deadline asc, id desc',
            limit=limit,
            offset=offset,
        )

        result = []
        now = datetime.now()
        for act in activities:
            # Determine if this activity has approve/reject actions
            can_approve = False
            if act.activity_type_id and act.activity_type_id.category == 'grant_approval':
                can_approve = True

            # Relative time
            delta = now - act.create_date
            if delta.days > 0:
                time_ago = _('%d days ago') % delta.days
            elif delta.seconds >= 3600:
                time_ago = _('%d hours ago') % (delta.seconds // 3600)
            else:
                mins = max(delta.seconds // 60, 1)
                time_ago = _('%d mins ago') % mins

            result.append({
                'id': act.id,
                'summary': act.summary or act.activity_type_id.name or _('Activity'),
                'res_name': act.res_name or '',
                'res_model': act.res_model,
                'res_id': act.res_id,
                'activity_type': act.activity_type_id.name if act.activity_type_id else '',
                'activity_category': act.activity_category or 'default',
                'date_deadline': str(act.date_deadline) if act.date_deadline else '',
                'time_ago': time_ago,
                'can_approve': can_approve,
                'icon': act.activity_type_id.icon if act.activity_type_id else 'fa-clock-o',
            })

        return {
            'activities': result,
            'total': total,
        }

    @http.route('/my/notifications/action', type='json', auth='user', methods=['POST'])
    def notification_action(self, activity_id, action, **kw):
        """Execute approve/reject on a mail.activity."""
        Activity = request.env['mail.activity'].sudo()
        activity = Activity.browse(int(activity_id))

        if not activity.exists() or activity.user_id.id != request.env.user.id:
            return {'success': False, 'error': _('Activity not found.')}

        if action == 'approve':
            activity.action_feedback(feedback=_('Approved via portal'))
        elif action == 'reject':
            activity.action_feedback(feedback=_('Rejected via portal'))
        else:
            return {'success': False, 'error': _('Invalid action.')}

        # Return updated count
        new_count = Activity.search_count([
            ('user_id', '=', request.env.user.id),
        ])

        return {'success': True, 'new_count': new_count}
