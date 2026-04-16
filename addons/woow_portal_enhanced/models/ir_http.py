# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _frontend_pre_dispatch(cls):
        """Override to respect the authenticated user's language preference.

        Odoo's http_routing sets ``request.lang`` inside ``_match()``
        (transaction 1), but between transactions the attribute can
        become stale — typically falling back to the default language
        because the ``frontend_lang`` cookie (set during login) wins
        over the session context in the priority chain.

        ``_frontend_pre_dispatch`` then stamps that stale value onto
        ``env.context``, overriding the correct ``lang`` that
        ``base._pre_dispatch`` already set from the session context.

        Without the ``website`` module installed there is no URL-based
        lang negotiation, so the session / user preference should always
        win.  We use the lang from ``env.context`` (which was correctly
        set by ``base._pre_dispatch`` via ``get_lang()``) and sync
        ``request.lang`` to match.
        """
        # Use the lang already present in env.context (set by
        # base._pre_dispatch → get_lang()) which honours the session.
        lang_code = request.env.context.get('lang', 'en_US')

        # Sync request.lang with the context value so downstream code
        # that reads request.lang (e.g. slug redirects) sees the right
        # language.
        request.lang = request.env['res.lang']._get_data(code=lang_code)

        # Keep frontend_lang cookie pointing at the *default* language
        # so that http_routing._match() never redirects to /<lang>/...
        # URLs (which break without the website module).  The actual
        # translation is handled entirely through env.context['lang'].
        default_lang = cls._get_default_lang()
        if request.cookies.get('frontend_lang') != default_lang.code:
            request.future_response.set_cookie('frontend_lang', default_lang.code)

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        mods = super()._get_translation_frontend_modules_name()
        return mods + ['woow_portal_enhanced']
