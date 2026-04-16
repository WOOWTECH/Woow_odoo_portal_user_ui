# -*- coding: utf-8 -*-
"""
Color Customizer - Settings Model
Extends res.config.settings to add primary color configuration.
"""
from odoo import api, fields, models

# Default Odoo Community purple color (from primary_variables.scss: $o-community-color)
DEFAULT_PRIMARY_COLOR = '#71639e'


class ResConfigSettings(models.TransientModel):
    """Extend General Settings with color customization options."""
    _inherit = 'res.config.settings'

    primary_color = fields.Char(
        string='Primary Color',
        config_parameter='odoo_color_customizer.primary_color',
        default=DEFAULT_PRIMARY_COLOR,
        help='Choose a custom primary color for the Odoo interface. '
             'This color will replace the default Odoo purple across the entire UI.'
    )

    def action_reset_primary_color(self):
        """Reset primary color to Odoo Community default (#71639e)."""
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_color_customizer.primary_color',
            DEFAULT_PRIMARY_COLOR
        )
        # Reload page to apply changes
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
