# -*- coding: utf-8 -*-
#
#  ┌────────────────────────────────────────────────────────────────┐
#  │   Developed by: Code Sparks                                    │
#  │   Website: https://code-sparks.odoo.com                        │
#  │   LinkedIn: https://www.linkedin.com/company/codesparks-tech   │
#  │   Description: Portal Collaboration, Chat & Meetings Hub       │
#  └────────────────────────────────────────────────────────────────┘
#
#  🔥 Empowering businesses with smart, compliant collaboration 💡

from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request


class PortalDiscussController(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'portal_discussion_count' in counters:
            partner = request.env.user.partner_id
            values['portal_discussion_count'] = request.env['discuss.channel'].sudo().search_count([
                ('channel_member_ids.partner_id', 'in', [partner.id]),
                '|',
                    ('channel_type', 'in', ('chat', 'group')),
                    '&',
                        ('channel_type', '=', 'channel'),
                        ('group_public_id', '=', request.env.ref('base.group_portal').id),
            ])
        return values

    def _get_portal_discussion_domain(self):
        partner = request.env.user.partner_id
        return [
            ('channel_member_ids.partner_id', 'in', [partner.id]),
            '|',
                ('channel_type', 'in', ('chat', 'group')),
                '&',
                    ('channel_type', '=', 'channel'),
                    ('group_public_id', '=', request.env.ref('base.group_portal').id),
        ]

    @http.route(['/my/discussions', '/my/discussions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_discussions(self, page=1, **kwargs):
        DiscussChannel = request.env['discuss.channel'].sudo()
        domain = self._get_portal_discussion_domain()

        discussion_count = DiscussChannel.search_count(domain)
        pager = portal_pager(
            url="/my/discussions",
            total=discussion_count,
            page=page,
            step=20,
        )
        channels = DiscussChannel.search(
            domain,
            order='create_date desc',
            limit=20,
            offset=pager['offset'],
        )

        return request.render(
            'cs_portal_discuss.portal_discuss_channels',
            {
                'channels': channels,
                'page_name': 'discussions',
                'pager': pager,
                'default_url': '/my/discussions',
            }
        )