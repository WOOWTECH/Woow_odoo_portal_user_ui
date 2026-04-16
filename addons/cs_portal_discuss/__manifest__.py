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

{
    "name": "Portal Discuss, Chat & Meetings Hub",
    "version": "18.0.0.0",
    "summary": (
        "Allow portal users to chat, join discussions, "
        "and attend meetings with internal users, groups, and channels."
    ),
    "description": """
        Portal Discuss, Chat & Meetings Hub extends Odoo's collaboration features
        to portal users, enabling secure and centralized communication without
        relying on external meeting or chat platforms.

        Key Features:
        • Portal users can communicate directly with internal users  
        • One-to-one chat with specific users  
        • Participate in group chats and discussion channels  
        • Send and receive messages in real time 
        • View and participate in meetings directly from Odoo  
        • Access chat history, shared notes, and meeting records  
        • Fully integrated with Odoo Discuss, Mail, Calendar  

        Business Use Case:
        In many countries, third-party meeting tools like Zoom or Google Meet are
        restricted or not allowed. This module enables companies to rely entirely
        on Odoo for meetings, discussions, and customer collaboration.

        Companies can create portal users for customers, partners, or external
        stakeholders, allowing them to attend meetings, communicate securely,
        and collaborate — all within Odoo.

        Ideal for:
        • Enterprises with compliance or data-residency requirements  
        • Customer collaboration portals  
        • Partner communication platforms  
        • Organizations seeking an all-in-one Odoo-based collaboration solution  
    """,
    "author": "Code Sparks",
    "company": "Code Sparks",
    "maintainer": "Code Sparks",
    "category": "Portal",
    "support": "info.codesparks@gmail.com",
    "website": "https://code-sparks.odoo.com",
    "depends": [
        "portal",
        "mail",
        "calendar",
        "web",
    ],
    "data": [
        "views/portal_discuss_template.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cs_portal_discuss/static/src/discuss/core/common/**/*",
        ],
        "mail.assets_public": [
            "cs_portal_discuss/static/src/**/public/**/*",
            "cs_portal_discuss/static/src/discuss/core/common/**/*",
        ],
    },
    "images": [
        "static/description/banner.gif"
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
    "price": 15,
    "currency": "USD",
}
