# -*- coding: utf-8 -*-

from datetime import datetime

import pytz
from babel.dates import format_date as babel_format_date

from odoo import _, http
from odoo.fields import Date as FieldDate, Datetime as FieldDatetime
from odoo.http import request
from odoo.tools import html2plaintext
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.web import Home

# If project module is installed, extend its controller instead of base
try:
    from odoo.addons.project.controllers.portal import ProjectCustomerPortal
    _PortalBase = ProjectCustomerPortal
except ImportError:
    _PortalBase = CustomerPortal

# Hard cap for pagination to prevent abuse
_MAX_LIMIT = 100


class WoowPortalUI(_PortalBase):

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
        if delta.days == 1:
            return _('1 day ago')
        elif delta.days > 1:
            return _('%d days ago') % delta.days
        elif delta.seconds >= 7200:
            return _('%d hours ago') % (delta.seconds // 3600)
        elif delta.seconds >= 3600:
            return _('1 hour ago')
        else:
            mins = max(delta.seconds // 60, 1)
            if mins == 1:
                return _('1 min ago')
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
        """Convert a mail.notification record to unified display dict."""
        msg = notif.mail_message_id
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
            'body_preview': self._extract_text_preview(msg.body, 200),
            'record_name': msg.record_name or '',
            'model': msg.model or '',
            'res_id': msg.res_id or 0,
            'author_name': msg.author_id.name if msg.author_id else _('System'),
            'date': msg.date.strftime('%Y-%m-%d %H:%M') if msg.date else '',
            'time_ago': self._relative_time(msg.date, now),
            'is_read': notif.is_read,
            'icon': icon,
            'document_url': self._get_document_portal_url(msg.model, msg.res_id),
            'subtype_name': msg.subtype_id.name if msg.subtype_id else '',
            'tracking_summary': tracking_summary,
            'message_type': msg.message_type or '',
        }

    def _activity_to_dict(self, act, now):
        """Convert a mail.activity record to unified display dict."""
        time_ago = self._relative_time(act.create_date, now)

        # Activity state based on deadline
        today = FieldDate.context_today(request.env.user)
        if act.date_deadline and act.date_deadline < today:
            state = 'overdue'
        elif act.date_deadline and act.date_deadline == today:
            state = 'today'
        else:
            state = 'planned'

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
            'state': state,
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
    # Greeting data
    # ------------------------------------------------------------------

    @staticmethod
    def _get_greeting_data():
        """Return greeting string and timezone-aware date/time info."""
        user_tz_name = request.env.user.tz or 'UTC'
        try:
            user_tz = pytz.timezone(user_tz_name)
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.UTC
        now_utc = datetime.now(pytz.UTC)
        now_local = now_utc.astimezone(user_tz)
        hour = now_local.hour

        if 6 <= hour < 12:
            greeting = _('Good Morning')
        elif 12 <= hour < 18:
            greeting = _('Good Afternoon')
        else:
            greeting = _('Good Evening')

        lang_code = request.env.user.lang or 'en_US'
        weekday_str = babel_format_date(
            now_local, format='EEE', locale=lang_code)

        utc_offset = now_local.strftime('%z')  # e.g. '+0800'
        offset_formatted = 'UTC%s%s' % (
            utc_offset[:3],
            '' if utc_offset[3:] == '00' else ':' + utc_offset[3:])

        return {
            'greeting': greeting,
            'today_date_line1': '%s (%s)' % (
                now_local.strftime('%Y-%m-%d'), weekday_str),
            'today_date_line2': '%s %s' % (
                now_local.strftime('%H:%M'), offset_formatted),
        }

    # ------------------------------------------------------------------
    # Notification preview data for portal home
    # ------------------------------------------------------------------

    def _prepare_notification_values(self):
        """Build notification preview data for the portal home page."""
        user = request.env.user
        partner = user.partner_id
        is_internal = user._is_internal()
        now = FieldDatetime.now()

        Notification = request.env['mail.notification'].sudo()
        notif_base = [('res_partner_id', '=', partner.id)]

        # Messages: comment / email
        msg_domain = notif_base + [
            ('is_read', '=', False),
            ('mail_message_id.message_type', 'in', ['comment', 'email']),
        ]
        unread_message_count = Notification.search_count(msg_domain)
        message_previews = [
            self._notif_to_dict(n, now)
            for n in Notification.search(
                msg_domain, order='mail_message_id desc', limit=2)
        ]

        # System notifications
        sys_domain = notif_base + [
            ('is_read', '=', False),
            ('mail_message_id.message_type', 'in',
             ['notification', 'auto_comment', 'user_notification']),
        ]
        unread_sys_notif_count = Notification.search_count(sys_domain)
        sys_notif_previews = [
            self._notif_to_dict(n, now)
            for n in Notification.search(
                sys_domain, order='mail_message_id desc', limit=2)
        ]

        # Activities (to-do): internal users only
        activity_count = 0
        activity_previews = []
        if is_internal:
            Activity = request.env['mail.activity'].sudo()
            act_domain = [('user_id', '=', user.id)]
            activity_count = Activity.search_count(act_domain)
            activity_previews = [
                self._activity_to_dict(act, now)
                for act in Activity.search(
                    act_domain, order='date_deadline asc, id desc', limit=2)
            ]

        total_unread = (unread_message_count + unread_sys_notif_count
                        + activity_count)

        greeting_data = self._get_greeting_data()

        return {
            'message_previews': message_previews,
            'unread_message_count': unread_message_count,
            'sys_notif_previews': sys_notif_previews,
            'unread_sys_notif_count': unread_sys_notif_count,
            'activity_previews': activity_previews,
            'activity_count': activity_count,
            'total_unread_count': total_unread,
            'is_internal_user': is_internal,
            'greeting': greeting_data['greeting'],
            'greeting_name': partner.name or user.name or '',
            'today_date_line1': greeting_data['today_date_line1'],
            'today_date_line2': greeting_data['today_date_line2'],
        }

    # ------------------------------------------------------------------
    # Language switch
    # ------------------------------------------------------------------

    @http.route('/my/set_lang/<string:lang_code>', type='http',
                auth='user', website=True, multilang=False)
    def set_language(self, lang_code, **kw):
        available = dict(request.env['res.lang'].get_installed())
        if lang_code not in available:
            return request.redirect('/my')
        request.env.user.sudo().write({'lang': lang_code})
        ctx = dict(request.session.get('context', {}))
        ctx['lang'] = lang_code
        request.session['context'] = ctx
        # Strip language prefix from referrer so http_routing picks up
        # the new language from the cookie instead of the old URL prefix.
        redirect_url = request.httprequest.referrer or '/my'
        try:
            from urllib.parse import urlparse
            path = urlparse(redirect_url).path
            lang_records = request.env['res.lang'].sudo().search(
                [('active', '=', True)])
            url_codes = set(lang_records.mapped('url_code'))
            parts = path.split('/')
            if len(parts) > 1 and parts[1] in url_codes:
                path = '/' + '/'.join(parts[2:]) or '/'
            redirect_url = path
        except Exception:
            redirect_url = '/my'
        response = request.redirect(redirect_url)
        response.set_cookie('frontend_lang', lang_code)
        return response

    # ------------------------------------------------------------------
    # Portal home override
    # ------------------------------------------------------------------

    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update(self._prepare_home_portal_values([]))
        values.update(self._prepare_notification_values())
        return request.render("portal.portal_my_home", values)

    # ------------------------------------------------------------------
    # Notification list page
    # ------------------------------------------------------------------

    @http.route('/my/notifications', type='http', auth='user',
                website=True, methods=['GET'])
    def notifications_page(self, tab='all', **kw):
        """Full notification list page with 4 tabs."""
        user = request.env.user
        partner = user.partner_id
        is_internal = user._is_internal()
        now = FieldDatetime.now()

        items = []

        Notification = request.env['mail.notification'].sudo()
        notif_base = [('res_partner_id', '=', partner.id)]

        if tab == 'message':
            domain = notif_base + [
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']),
            ]
            notifs = Notification.search(
                domain, order='mail_message_id desc', limit=_MAX_LIMIT)
            for n in notifs:
                items.append(self._notif_to_dict(n, now))

        elif tab == 'notification':
            domain = notif_base + [
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']),
            ]
            notifs = Notification.search(
                domain, order='mail_message_id desc', limit=_MAX_LIMIT)
            for n in notifs:
                items.append(self._notif_to_dict(n, now))

        elif tab == 'activity':
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
        unread_notif = Notification.search_count(
            notif_base + [('is_read', '=', False)])

        unread_message_count = Notification.search_count(
            notif_base + [
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']),
            ])
        unread_sys_notif_count = Notification.search_count(
            notif_base + [
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']),
            ])

        activity_count = 0
        if is_internal:
            Activity = request.env['mail.activity'].sudo()
            activity_count = Activity.search_count([
                ('user_id', '=', user.id)])

        values = self._prepare_portal_layout_values()
        values.update({
            'notification_items': items,
            'unread_notif_count': unread_notif,
            'unread_all_count': unread_notif + activity_count,
            'unread_message_count': unread_message_count,
            'unread_sys_notif_count': unread_sys_notif_count,
            'activity_count': activity_count,
            'current_tab': tab,
            'is_internal_user': is_internal,
            'page_name': 'notifications',
        })
        return request.render(
            'woow_portal_ui.portal_notifications_page', values)

    # ------------------------------------------------------------------
    # JSON-RPC: notification data
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
                ('is_read', '=', False),
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
                ('is_read', '=', False),
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

        unread_msg_count = Notification.search_count(
            notif_base + [
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']),
            ])
        unread_notif_count = Notification.search_count(
            notif_base + [
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']),
            ])

        return {
            'notifications': items,
            'total': total,
            'unread_count': unread_msg_count + unread_notif_count,
            'unread_message_count': unread_msg_count,
            'unread_notification_count': unread_notif_count,
        }

    # ------------------------------------------------------------------
    # JSON-RPC: notification actions
    # ------------------------------------------------------------------

    @http.route('/my/notifications/action', type='json', auth='user',
                methods=['POST'])
    def notification_action(self, notification_id=None, activity_id=None,
                            action=None, **kw):
        """Handle mark_read/mark_unread or done/approve/reject."""

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
            elif action == 'dismiss':
                # Permanently remove a read notification so it won't
                # reappear on page reload.  The underlying mail.message
                # is preserved — only the per-partner link is deleted.
                if not notif.is_read:
                    # Safety: refuse to dismiss unread notifications
                    return {'success': False,
                            'error': _('Cannot dismiss unread notification.')}
                notif.unlink()
            else:
                return {'success': False, 'error': _('Invalid action.')}

            new_msg_unread = Notification.search_count([
                ('res_partner_id', '=', partner.id),
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']),
            ])
            new_notif_unread = Notification.search_count([
                ('res_partner_id', '=', partner.id),
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']),
            ])
            return {
                'success': True,
                'unread_count': new_msg_unread + new_notif_unread,
                'unread_message_count': new_msg_unread,
                'unread_notification_count': new_notif_unread,
            }

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
            partner = request.env.user.partner_id
            Notification = request.env['mail.notification'].sudo()
            new_msg_unread = Notification.search_count([
                ('res_partner_id', '=', partner.id),
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']),
            ])
            new_notif_unread = Notification.search_count([
                ('res_partner_id', '=', partner.id),
                ('is_read', '=', False),
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']),
            ])
            return {
                'success': True,
                'activity_count': new_count,
                'unread_count': new_msg_unread + new_notif_unread,
                'unread_message_count': new_msg_unread,
                'unread_notification_count': new_notif_unread,
            }

        return {'success': False, 'error': _('Missing ID parameter.')}

    # ------------------------------------------------------------------
    # JSON-RPC: mark all read
    # ------------------------------------------------------------------

    @http.route('/my/notifications/mark_all_read', type='json',
                auth='user', methods=['POST'])
    def mark_all_read(self, tab=None, **kw):
        """Mark unread notifications as read, scoped to the given tab."""
        partner = request.env.user.partner_id
        Notification = request.env['mail.notification'].sudo()
        domain = [
            ('res_partner_id', '=', partner.id),
            ('is_read', '=', False),
        ]
        if tab == 'message':
            domain.append(
                ('mail_message_id.message_type', 'in',
                 ['comment', 'email']))
        elif tab == 'notification':
            domain.append(
                ('mail_message_id.message_type', 'in',
                 ['notification', 'auto_comment', 'user_notification']))
        # 'all' or None → no additional filter (marks everything)

        unread = Notification.search(domain)
        if unread:
            unread.write({
                'is_read': True,
                'read_date': FieldDatetime.now(),
            })

        # Return separate counts after update
        new_msg_unread = Notification.search_count([
            ('res_partner_id', '=', partner.id),
            ('is_read', '=', False),
            ('mail_message_id.message_type', 'in', ['comment', 'email']),
        ])
        new_notif_unread = Notification.search_count([
            ('res_partner_id', '=', partner.id),
            ('is_read', '=', False),
            ('mail_message_id.message_type', 'in',
             ['notification', 'auto_comment', 'user_notification']),
        ])
        activity_count = 0
        if request.env.user._is_internal():
            activity_count = request.env['mail.activity'].sudo().search_count(
                [('user_id', '=', request.env.user.id)])
        return {
            'success': True,
            'updated': len(unread),
            'unread_count': new_msg_unread + new_notif_unread,
            'unread_message_count': new_msg_unread,
            'unread_notification_count': new_notif_unread,
            'activity_count': activity_count,
        }

    # ------------------------------------------------------------------
    # JSON-RPC: notification detail (modal)
    # ------------------------------------------------------------------

    @http.route('/my/notifications/detail', type='json', auth='user',
                methods=['POST'])
    def notification_detail(self, notification_id=None, activity_id=None,
                            **kw):
        """Return full detail for the modal view."""

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
                    'date': msg.date.strftime('%Y-%m-%d %H:%M') if msg.date else '',
                    'is_read': notif.is_read,
                    'document_url': self._get_document_portal_url(
                        msg.model, msg.res_id),
                    'subtype_name': (msg.subtype_id.name
                                     if msg.subtype_id else ''),
                    'message_type': msg.message_type,
                    'tracking_details': tracking_details,
                },
            }

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

    # ------------------------------------------------------------------
    # Project portal override (only active when project module installed)
    # ------------------------------------------------------------------

    if _PortalBase is not CustomerPortal:
        # Override: always render portal-style template (skip iframe)
        @http.route()
        def portal_my_project(self, project_id=None, access_token=None,
                              page=1, date_begin=None, date_end=None,
                              sortby=None, search=None, search_in='content',
                              groupby=None, task_id=None, **kw):
            try:
                project_sudo = self._document_check_access(
                    'project.project', project_id, access_token)
            except Exception:
                return request.redirect('/my')

            is_editor = bool(
                project_sudo.collaborator_count
                and project_sudo.with_user(
                    request.env.user)._check_project_sharing_access()
            )

            project_sudo = (project_sudo if access_token
                            else project_sudo.with_user(request.env.user))
            if not groupby:
                groupby = 'stage_id'
            values = self._project_get_page_view_values(
                project_sudo, access_token, page, date_begin, date_end,
                sortby, search, search_in, groupby, **kw)
            values['is_editor'] = is_editor

            if is_editor:
                stages = request.env['project.task.type'].sudo().search(
                    [('project_ids', 'in', [project_id])])
                values['available_stages'] = stages

            return request.render("project.portal_my_project", values)

        @http.route()
        def portal_my_project_task(self, project_id=None, task_id=None,
                                    access_token=None, **kw):
            """Override to inject is_editor and available_stages."""
            try:
                project_sudo = self._document_check_access(
                    'project.project', project_id, access_token)
            except Exception:
                return request.redirect('/my')

            is_editor = bool(
                project_sudo.collaborator_count
                and project_sudo.with_user(
                    request.env.user)._check_project_sharing_access()
            )

            Task = request.env['project.task']
            if access_token:
                Task = Task.sudo()
            task_sudo = Task.search(
                [('project_id', '=', project_id), ('id', '=', task_id)],
                limit=1).sudo()
            task_sudo.attachment_ids.generate_access_token()
            values = self._task_get_page_view_values(
                task_sudo, access_token, project=project_sudo, **kw)
            values['project'] = project_sudo
            values['is_editor'] = is_editor

            # If this task is a sub-task, pass parent for breadcrumb
            if task_sudo.parent_id:
                values['parent_task'] = task_sudo.parent_id

            if is_editor:
                values['available_stages'] = (
                    request.env['project.task.type'].sudo().search(
                        [('project_ids', 'in', [project_id])]))
                values['available_milestones'] = (
                    request.env['project.milestone'].sudo().search(
                        [('project_id', '=', project_id)])
                    if hasattr(request.env['project.task'], 'milestone_id')
                    else [])

            return request.render("project.portal_my_task", values)

        @http.route('/my/projects/<int:project_id>/task/<int:task_id>/update',
                    type='json', auth='user', methods=['POST'])
        def project_update_task(self, project_id, task_id, **kw):
            """Update task fields (editor access required)."""
            project = request.env['project.project'].sudo().browse(project_id)
            if (not project.exists()
                    or not project.with_user(
                        request.env.user)._check_project_sharing_access()):
                return {'success': False, 'error': _('Access denied.')}

            task = request.env['project.task'].sudo().search(
                [('project_id', '=', project_id), ('id', '=', task_id)],
                limit=1)
            if not task:
                return {'success': False, 'error': _('Task not found.')}

            allowed = {'name', 'stage_id', 'priority', 'date_deadline',
                       'milestone_id', 'description'}
            vals = {}
            for field in allowed:
                if field in kw:
                    val = kw[field]
                    if field in ('stage_id', 'milestone_id'):
                        vals[field] = int(val) if val else False
                    elif field == 'priority':
                        vals[field] = str(val)
                    elif field == 'date_deadline':
                        vals[field] = val.replace('T', ' ') if val else False
                    else:
                        vals[field] = val

            if vals:
                task.write(vals)
            return {'success': True}

        @http.route('/my/projects/<int:project_id>/add_task',
                    type='json', auth='user', methods=['POST'])
        def project_add_task(self, project_id, name, stage_id=None, **kw):
            """Create a new task in the project (editor access required)."""
            project = request.env['project.project'].sudo().browse(project_id)
            if (not project.exists()
                    or not project.with_user(
                        request.env.user)._check_project_sharing_access()):
                return {'success': False, 'error': _('Access denied.')}
            vals = {
                'name': name,
                'project_id': project_id,
            }
            if stage_id:
                vals['stage_id'] = int(stage_id)
            task = request.env['project.task'].sudo().create(vals)
            return {'success': True, 'task_id': task.id}

        @http.route('/my/projects/<int:project_id>/add_stage',
                    type='json', auth='user', methods=['POST'])
        def project_add_stage(self, project_id, name, **kw):
            """Create a new stage for the project (editor access required)."""
            project = request.env['project.project'].sudo().browse(project_id)
            if (not project.exists()
                    or not project.with_user(
                        request.env.user)._check_project_sharing_access()):
                return {'success': False, 'error': _('Access denied.')}
            # Set sequence after the last existing stage
            TaskType = request.env['project.task.type'].sudo()
            last_stage = TaskType.search(
                [('project_ids', 'in', [project_id])],
                order='sequence desc, id desc', limit=1)
            max_seq = last_stage.sequence if last_stage else 0
            stage = TaskType.create({
                'name': name,
                'sequence': max_seq + 1,
                'project_ids': [(4, project_id)],
            })
            return {'success': True, 'stage_id': stage.id}

        @http.route(
            '/my/projects/<int:project_id>/task/<int:task_id>/add_subtask',
            type='json', auth='user', methods=['POST'])
        def project_add_subtask(self, project_id, task_id, name,
                                stage_id=None, date_deadline=None,
                                description=None, **kw):
            """Create a sub-task linked to the parent task."""
            project = request.env['project.project'].sudo().browse(project_id)
            if (not project.exists()
                    or not project.with_user(
                        request.env.user)._check_project_sharing_access()):
                return {'success': False, 'error': _('Access denied.')}
            parent = request.env['project.task'].sudo().search(
                [('project_id', '=', project_id), ('id', '=', task_id)],
                limit=1)
            if not parent:
                return {'success': False, 'error': _('Task not found.')}
            vals = {
                'name': name,
                'project_id': project_id,
                'parent_id': task_id,
            }
            if stage_id:
                vals['stage_id'] = int(stage_id)
            if date_deadline:
                vals['date_deadline'] = date_deadline.replace('T', ' ')
            if description:
                vals['description'] = description
            subtask = request.env['project.task'].sudo().create(vals)
            return {'success': True, 'subtask_id': subtask.id}

        @http.route(
            '/my/projects/<int:project_id>/task/<int:task_id>/delete_subtask',
            type='json', auth='user', methods=['POST'])
        def project_delete_subtask(self, project_id, task_id,
                                    subtask_id, **kw):
            """Delete a sub-task of the given parent task."""
            project = request.env['project.project'].sudo().browse(project_id)
            if (not project.exists()
                    or not project.with_user(
                        request.env.user)._check_project_sharing_access()):
                return {'success': False, 'error': _('Access denied.')}
            subtask = request.env['project.task'].sudo().search([
                ('id', '=', int(subtask_id)),
                ('parent_id', '=', task_id),
                ('project_id', '=', project_id),
            ], limit=1)
            if not subtask:
                return {'success': False, 'error': _('Sub-task not found.')}
            subtask.unlink()
            return {'success': True}


class WoowHome(Home):
    """Redirect all users to portal home after login."""

    def _login_redirect(self, uid, redirect=None):
        # Only override when the user did not explicitly request a redirect
        # (e.g. via deep link). Check the original form/query parameter
        # instead of the `redirect` argument, which may have been pre-set
        # by another module (e.g. website) earlier in the MRO chain.
        if not request.params.get('redirect'):
            redirect = '/my/home'
        return super()._login_redirect(uid, redirect)
