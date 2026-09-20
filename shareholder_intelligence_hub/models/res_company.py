# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    dashboard_ebitda_target = fields.Float(
        string='EBITDA Margin Target (%)', default=25.0,
        help='Management benchmark threshold. See Section 4.1: '
             '"Management target: > 25.0%".',
    )
    dashboard_cash_runway_target_months = fields.Float(
        string='Target Cash Runway (months)', default=6.0,
    )

    dashboard_fx_method = fields.Selection(
        selection=[
            ('closing', 'Closing exchange rate'),
            ('average', 'Period average exchange rate'),
        ],
        string='FX Conversion Method', default='closing',
        help='Method used when consolidating subsidiaries with a currency '
             'different from the corporate currency. See Section 6.1.',
    )
    dashboard_eliminate_intercompany = fields.Boolean(
        string='Eliminate Intercompany Transactions',
        default=True,
        help='If active, sales/purchases between subsidiaries of the same '
             'group are excluded from the consolidated view to avoid artificially '
             'inflating revenue (Section 6.1).',
    )
