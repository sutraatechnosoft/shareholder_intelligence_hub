# -*- coding: utf-8 -*-
from odoo import fields, models


class DashboardConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dashboard_ebitda_target = fields.Float(
        related='company_id.dashboard_ebitda_target', readonly=False,
        string='EBITDA Margin Target (%)',
    )
    dashboard_cash_runway_target_months = fields.Float(
        related='company_id.dashboard_cash_runway_target_months',
        readonly=False, string='Target Cash Runway (months)',
    )
    dashboard_fx_method = fields.Selection(
        related='company_id.dashboard_fx_method', readonly=False,
        string='FX Conversion Method',
    )
    dashboard_eliminate_intercompany = fields.Boolean(
        related='company_id.dashboard_eliminate_intercompany',
        readonly=False, string='Eliminate Intercompany Transactions',
    )