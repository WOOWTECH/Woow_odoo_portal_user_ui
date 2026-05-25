from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        mods = super()._get_translation_frontend_modules_name()
        return mods + ["woow_portal_ui"]

    @classmethod
    def _frontend_pre_dispatch(cls):
        super()._frontend_pre_dispatch()
        # For logged-in users, respect their stored language preference
        # even when the website module doesn't include it in its
        # language list.  This lets portal users switch language freely
        # based on system-active languages without modifying website
        # configuration.
        if not request.env.user._is_public():
            user_lang = request.env.user.lang
            if user_lang and user_lang != request.env.context.get('lang'):
                installed = dict(request.env['res.lang'].get_installed())
                if user_lang in installed:
                    request.update_context(lang=user_lang)
                    request.future_response.set_cookie(
                        'frontend_lang', user_lang)
