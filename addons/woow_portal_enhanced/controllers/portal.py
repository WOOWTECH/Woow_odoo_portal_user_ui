# -*- coding: utf-8 -*-

from odoo import _, http
from odoo.fields import Datetime as FieldDatetime
from odoo.http import request
from odoo.tools import html2plaintext
from odoo.addons.portal.controllers.portal import CustomerPortal

# Hard cap for pagination to prevent abuse
_MAX_LIMIT = 100


class WoowPortalEnhanced(CustomerPortal):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text_preview(html_body, max_chars=80):
        """Strip HTML tags and truncate for preview display."""
        if not html_body:
            return ''
        text = html2plaintext(html_body).strip()
        if len(text) > max_chars:
            return text[:max_chars].rstrip() + '...'
        return text

    @staticmethod
    def _get_document_portal_url(model, res_id):
        """Resolve portal URL for a model/res_id pair."""
        if not model or not res_id:
            return '#'
        try:
            env_model = request.env[model]
        except KeyError:
            return '#'
        record = env_model.sudo().browse(res_id)
        if not record.exists():
            return '#'
        if hasattr(record, 'access_url'):
            url = record.access_url
            if url and url != '#':
                return url
        return '#'

    @staticmethod
    def _relative_time(dt_from, dt_to):
        """Return a relative time string (e.g. '3 days ago')."""
        if not dt_from or not dt_to:
            return ''
        delta = dt_to - dt_from
        if delta.days > 0:
            return _('%d days ago') % delta.days
        elif delta.seconds >= 3600:
            return _('%d hours ago') % (delta.seconds // 3600)
        else:
            mins = max(delta.seconds // 60, 1)
            return _('%d mins ago') % mins

    def _build_tracking_summary(self, tracking_values):
        """Readable summary from tracking value changes (requires sudo)."""
        parts = []
        for tv in tracking_values.sudo():
            field_name = tv.field_id.field_description if tv.field_id else ''
            old_val = tv.old_value_char or (
                str(tv.old_value_integer) if tv.old_value_integer else '')
            new_val = tv.new_value_char or (
                str(tv.new_value_integer) if tv.new_value_integer else '')
            if old_val and new_val:
                parts.append('%s: %s → %s' % (field_name, old_val, new_val))
            elif new_val:
                parts.append('%s: %s' % (field_name, new_val))
        return '; '.join(parts)

    def _notif_to_dict(self, notif, now):
        """Convert a mail.notification record to display dict."""
        msg = notif.mail_message_id
        # Icon based on message content
        if msg.tracking_value_ids:
            icon = 'fa-exchange'
        elif msg.message_type == 'comment':
            icon = 'fa-comment'
        else:
            icon = 'fa-bell'

        tracking_summary = ''
        if msg.tracking_value_ids:
            tracking_summary = self._build_tracking_summary(
                msg.tracking_value_ids)

        return {
            'notif_id': notif.id,
            'message_id': msg.id,
            'subject': msg.subject or msg.record_name or _('Notification'),
            'body_preview': self._extract_text_preview(msg.body, 120),
            'record_name': msg.record_name or '',
            'model': msg.model or '',
            'res_id': msg.res_id or 0,
            'author_name': msg.author_id.name if msg.author_id else _('System'),
            'date': str(msg.date) if msg.date else '',
            'time_ago': self._relative_time(msg.date, now),
            'is_read': notif.is_read,
            'icon': icon,
            'document_url': self._get_document_portal_url(msg.model, msg.res_id),
            'subtype_name': msg.subtype_id.name if msg.subtype_id else '',
            'tracking_summary': tracking_summary,
            'message_type': msg.message_type or '',
        }

    def _activity_to_dict(self, act, now):
        """Convert a mail.activity record to display dict."""
        delta = now - act.create_date
        if delta.days > 0:
            time_ago = _('%d days ago') % delta.days
        elif delta.seconds >= 3600:
            time_ago = _('%d hours ago') % (delta.seconds // 3600)
        else:
            mins = max(delta.seconds // 60, 1)
            time_ago = _('%d mins ago') % mins

        return {
            'activity_id': act.id,
            'summary': (act.summary or act.activity_type_id.name
                        or _('Activity')),
            'res_name': act.res_name or '',
            'res_model': act.res_model,
            'res_id': act.res_id,
            'activity_type': (act.activity_type_id.name
                              if act.activity_type_id else ''),
            'activity_category': act.activity_category or 'default',
            'date_deadline': (str(act.date_deadline)
                              if act.date_deadline else ''),
            'time_ago': time_ago,
            'can_approve': bool(
                act.activity_type_id
                and act.activity_type_id.category == 'grant_approval'),
            'icon': (act.activity_type_id.icon
                     if act.activity_type_id else 'fa-clock-o'),
            'document_url': self._get_document_portal_url(
                act.res_model, act.res_id),
        }

    # ------------------------------------------------------------------
    # Inject notification data into portal home
    # ------------------------------------------------------------------

    def _prepare_home_portal_values(self, counters):
        """Extend portal home values with notification preview data."""
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        partner = user.partner_id
        is_internal = user._is_internal()
        now = FieldDatetime.now()

        # --- Mail Notification (unread) for preview ---
        Notification = request.env['mail.notification'].sudo()
        notif_domain = [
            ('res_partner_id', '=', partner.id),
            ('is_read', '=', False),
        ]
        notif_records = Notification.search(
            notif_domain, order='mail_message_id desc', limit=3)
        unread_notif_count = Notification.search_count(notif_domain)

        preview_items = []
        for notif in notif_records:
            preview_items.append(self._notif_to_dict(notif, now))

        # --- Mail Activity count (internal users only) ---
        activity_count = 0
        if is_internal:
            Activity = request.env['mail.activity'].sudo()
            activity_count = Activity.search_count([
                ('user_id', '=', user.id),
            ])

        values.update({
            'notification_previews': preview_items,
            'unread_notif_count': unread_notif_count,
            'activity_count': activity_count,
            'is_internal_user': is_internal,
        })
        return values

    # ------------------------------------------------------------------
    # Notification list page (full page, HTTP GET)
    # ------------------------------------------------------------------

    @http.route('/my/notifications', type='http', auth='user',
                website=True, methods=['GET'])
    def notifications_page(self, tab='all', **kw):
        """Full notification list page with 3 tabs.

        Tabs:
        - message:      mail.message (comments/discussions)
        - notification: mail.notification (unread system notifications)
        - activity:     mail.activity (internal users only)
        - all:          combined view (default)
        """
        user = request.env.user
        partner = user.partner_id
        is_internal = user._is_internal()
        now = FieldDatetime.now()

        items = []

        # Determine which tabs to show and query
        Notification = request.env['mail.notification'].sudo()
        notif_base = [('res_partner_id', '=', partner.id)]

        if tab == 'message':
            # mail.notification records whose message is a comment
            domain = notif_base + [
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']),
            ]
            notifs = Notification.search(
                domain, order='mail_message_id desc', limit=_MAX_LIMIT)
            for n in notifs:
                items.append(self._notif_to_dict(n, now))

        elif tab == 'notification':
            # mail.notification records whose message is system/tracking
            domain = notif_base + [
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']),
            ]
            notifs = Notification.search(
                domain, order='mail_message_id desc', limit=_MAX_LIMIT)
            for n in notifs:
                items.append(self._notif_to_dict(n, now))

        elif tab == 'activity':
            # mail.activity (internal users only)
            if is_internal:
                Activity = request.env['mail.activity'].sudo()
                activities = Activity.search(
                    [('user_id', '=', user.id)],
                    order='date_deadline asc, id desc',
                    limit=_MAX_LIMIT,
                )
                for act in activities:
                    items.append(self._activity_to_dict(act, now))

        else:
            # 'all' — combine notification + activity
            notifs = Notification.search(
                notif_base, order='mail_message_id desc', limit=_MAX_LIMIT)
            for n in notifs:
                items.append(self._notif_to_dict(n, now))

            if is_internal:
                Activity = request.env['mail.activity'].sudo()
                activities = Activity.search(
                    [('user_id', '=', user.id)],
                    order='date_deadline asc, id desc',
                    limit=_MAX_LIMIT,
                )
                for act in activities:
                    items.append(self._activity_to_dict(act, now))

        # Counts for tab badges
        total_notif = Notification.search_count(notif_base)
        unread_notif = Notification.search_count(
            notif_base + [('is_read', '=', False)])

        message_count = Notification.search_count(
            notif_base + [('mail_message_id.message_type', 'in',
                           ['comment', 'email'])])
        sys_notif_count = Notification.search_count(
            notif_base + [('mail_message_id.message_type', 'in',
                           ['notification', 'auto_comment',
                            'user_notification'])])

        activity_count = 0
        if is_internal:
            Activity = request.env['mail.activity'].sudo()
            activity_count = Activity.search_count([
                ('user_id', '=', user.id)])

        values = self._prepare_portal_layout_values()
        values.update({
            'notification_items': items,
            'notification_total': total_notif + activity_count,
            'unread_notif_count': unread_notif,
            'message_count': message_count,
            'sys_notif_count': sys_notif_count,
            'activity_count': activity_count,
            'current_tab': tab,
            'is_internal_user': is_internal,
            'page_name': 'notifications',
        })
        return request.render(
            'woow_portal_enhanced.portal_notifications_page', values)

    # ------------------------------------------------------------------
    # JSON-RPC endpoint for notification data
    # ------------------------------------------------------------------

    @http.route('/my/notifications/data', type='json', auth='user',
                methods=['POST'])
    def get_notifications(self, tab='all', limit=20, offset=0, **kw):
        """Return notification list as JSON for dynamic loading."""
        user = request.env.user
        partner = user.partner_id
        is_internal = user._is_internal()
        now = FieldDatetime.now()

        limit = max(0, min(int(limit), _MAX_LIMIT))
        offset = max(0, int(offset))

        Notification = request.env['mail.notification'].sudo()
        notif_base = [('res_partner_id', '=', partner.id)]

        items = []

        if tab == 'message':
            domain = notif_base + [
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']),
            ]
            total = Notification.search_count(domain)
            if limit > 0:
                notifs = Notification.search(
                    domain, order='mail_message_id desc',
                    limit=limit, offset=offset)
                for n in notifs:
                    items.append(self._notif_to_dict(n, now))

        elif tab == 'notification':
            domain = notif_base + [
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']),
            ]
            total = Notification.search_count(domain)
            if limit > 0:
                notifs = Notification.search(
                    domain, order='mail_message_id desc',
                    limit=limit, offset=offset)
                for n in notifs:
                    items.append(self._notif_to_dict(n, now))

        elif tab == 'activity':
            if is_internal:
                Activity = request.env['mail.activity'].sudo()
                act_domain = [('user_id', '=', user.id)]
                total = Activity.search_count(act_domain)
                if limit > 0:
                    activities = Activity.search(
                        act_domain, order='date_deadline asc, id desc',
                        limit=limit, offset=offset)
                    for act in activities:
                        items.append(self._activity_to_dict(act, now))
            else:
                total = 0

        else:
            # 'all' — combined
            notif_total = Notification.search_count(notif_base)
            act_total = 0
            if is_internal:
                Activity = request.env['mail.activity'].sudo()
                act_total = Activity.search_count([
                    ('user_id', '=', user.id)])
            total = notif_total + act_total

            if limit > 0:
                notifs = Notification.search(
                    notif_base, order='mail_message_id desc',
                    limit=limit, offset=offset)
                for n in notifs:
                    items.append(self._notif_to_dict(n, now))

                # If we have room left, also fetch activities
                remaining = limit - len(items)
                act_offset = max(0, offset - notif_total)
                if is_internal and remaining > 0 and offset + limit > notif_total:
                    Activity = request.env['mail.activity'].sudo()
                    activities = Activity.search(
                        [('user_id', '=', user.id)],
                        order='date_deadline asc, id desc',
                        limit=remaining, offset=act_offset)
                    for act in activities:
                        items.append(self._activity_to_dict(act, now))

        # Unread count (always useful for badges)
        unread_count = Notification.search_count(
            notif_base + [('is_read', '=', False)])

        return {
            'notifications': items,
            'total': total,
            'unread_count': unread_count,
        }

    # ------------------------------------------------------------------
    # JSON-RPC endpoint for notification actions
    # ------------------------------------------------------------------

    @http.route('/my/notifications/action', type='json', auth='user',
                methods=['POST'])
    def notification_action(self, notification_id=None, activity_id=None,
                            action=None, **kw):
        """Handle mark_read/mark_unread on mail.notification,
        or done/approve/reject on mail.activity."""

        # --- mail.notification actions ---
        if notification_id is not None:
            try:
                notification_id = int(notification_id)
            except (TypeError, ValueError):
                return {'success': False,
                        'error': _('Invalid notification ID.')}

            partner = request.env.user.partner_id
            Notification = request.env['mail.notification'].sudo()
            notif = Notification.browse(notification_id)

            if not notif.exists() or notif.res_partner_id.id != partner.id:
                return {'success': False,
                        'error': _('Notification not found.')}

            if action == 'mark_read':
                notif.write({
                    'is_read': True,
                    'read_date': FieldDatetime.now(),
                })
            elif action == 'mark_unread':
                notif.write({
                    'is_read': False,
                    'read_date': False,
                })
            else:
                return {'success': False, 'error': _('Invalid action.')}

            new_unread = Notification.search_count([
                ('res_partner_id', '=', partner.id),
                ('is_read', '=', False),
            ])
            return {'success': True, 'unread_count': new_unread}

        # --- mail.activity actions ---
        if activity_id is not None:
            try:
                activity_id = int(activity_id)
            except (TypeError, ValueError):
                return {'success': False,
                        'error': _('Invalid activity ID.')}

            Activity = request.env['mail.activity'].sudo()
            activity = Activity.browse(activity_id)

            if (not activity.exists()
                    or activity.user_id.id != request.env.user.id):
                return {'success': False,
                        'error': _('Activity not found.')}

            if action == 'done':
                activity.action_feedback(
                    feedback=_('Marked as done via portal'))
            elif action == 'approve':
                activity.action_feedback(
                    feedback=_('Approved via portal'))
            elif action == 'reject':
                activity.action_cancel()
            else:
                return {'success': False, 'error': _('Invalid action.')}

            new_count = Activity.search_count([
                ('user_id', '=', request.env.user.id),
            ])
            return {'success': True, 'new_count': new_count}

        return {'success': False, 'error': _('Missing ID parameter.')}

    # ------------------------------------------------------------------
    # JSON-RPC endpoint for notification detail (modal)
    # ------------------------------------------------------------------

    @http.route('/my/notifications/detail', type='json', auth='user',
                methods=['POST'])
    def notification_detail(self, notification_id=None, activity_id=None,
                            **kw):
        """Return full detail for the modal view."""

        # --- mail.notification detail ---
        if notification_id is not None:
            try:
                notification_id = int(notification_id)
            except (TypeError, ValueError):
                return {'success': False,
                        'error': _('Invalid notification ID.')}

            partner = request.env.user.partner_id
            Notification = request.env['mail.notification'].sudo()
            notif = Notification.browse(notification_id)

            if not notif.exists() or notif.res_partner_id.id != partner.id:
                return {'success': False,
                        'error': _('Notification not found.')}

            msg = notif.mail_message_id

            tracking_details = []
            for tv in msg.tracking_value_ids.sudo():
                tracking_details.append({
                    'field_name': (tv.field_id.field_description
                                   if tv.field_id else ''),
                    'old_value': tv.old_value_char or (
                        str(tv.old_value_integer)
                        if tv.old_value_integer else ''),
                    'new_value': tv.new_value_char or (
                        str(tv.new_value_integer)
                        if tv.new_value_integer else ''),
                })

            return {
                'success': True,
                'type': 'notification',
                'detail': {
                    'notif_id': notif.id,
                    'message_id': msg.id,
                    'subject': (msg.subject or msg.record_name
                                or _('Notification')),
                    'body': msg.body or '',
                    'record_name': msg.record_name or '',
                    'model': msg.model or '',
                    'res_id': msg.res_id or 0,
                    'author_name': (msg.author_id.name if msg.author_id
                                    else _('System')),
                    'author_avatar_url': (
                        '/web/image/res.partner/%d/avatar_128'
                        % msg.author_id.id if msg.author_id else ''),
                    'date': str(msg.date) if msg.date else '',
                    'is_read': notif.is_read,
                    'document_url': self._get_document_portal_url(
                        msg.model, msg.res_id),
                    'subtype_name': (msg.subtype_id.name
                                     if msg.subtype_id else ''),
                    'message_type': msg.message_type,
                    'tracking_details': tracking_details,
                },
            }

        # --- mail.activity detail ---
        if activity_id is not None:
            try:
                activity_id = int(activity_id)
            except (TypeError, ValueError):
                return {'success': False,
                        'error': _('Invalid activity ID.')}

            Activity = request.env['mail.activity'].sudo()
            activity = Activity.browse(activity_id)

            if (not activity.exists()
                    or activity.user_id.id != request.env.user.id):
                return {'success': False,
                        'error': _('Activity not found.')}

            return {
                'success': True,
                'type': 'activity',
                'detail': {
                    'activity_id': activity.id,
                    'summary': (activity.summary
                                or activity.activity_type_id.name
                                or _('Activity')),
                    'note': activity.note or '',
                    'res_name': activity.res_name or '',
                    'res_model': activity.res_model,
                    'res_id': activity.res_id,
                    'activity_type': (activity.activity_type_id.name
                                      if activity.activity_type_id else ''),
                    'date_deadline': (str(activity.date_deadline)
                                     if activity.date_deadline else ''),
                    'can_approve': bool(
                        activity.activity_type_id
                        and activity.activity_type_id.category
                        == 'grant_approval'),
                    'icon': (activity.activity_type_id.icon
                             if activity.activity_type_id else 'fa-clock-o'),
                    'document_url': self._get_document_portal_url(
                        activity.res_model, activity.res_id),
                },
            }

        return {'success': False, 'error': _('Missing ID parameter.')}
