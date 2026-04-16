# -*- coding: utf-8 -*-
{
    'name': 'Woow Portal Enhanced',
    'version': '18.0.1.1.0',
    'category': 'Website/Portal',
    'summary': 'Enhanced portal experience with app-like UI for portal and backend users',
    'description': """
Woow Portal Enhanced
====================
Enhances the Odoo 18 Portal with an app-like user experience:

- Global search bar for quick module navigation
- Notification center powered by mail.activity
- Redesigned module card grid (replaces "My Account")
- Backend ↔ Portal switch for admin users
- Responsive design (mobile / tablet)
    """,
    'author': 'WoowTech',
    'website': 'https://www.woowtech.com',
    'depends': ['portal', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'woow_portal_enhanced/static/src/css/portal.css',
            'woow_portal_enhanced/static/src/js/portal.js',
        ],
        'web.assets_backend': [
            'woow_portal_enhanced/static/src/js/switch_portal.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
