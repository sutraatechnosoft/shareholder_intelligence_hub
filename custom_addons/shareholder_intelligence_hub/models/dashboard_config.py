# -*- coding: utf-8 -*-
from odoo import fields, models


class DashboardConfigSettings(models.TransientModel):
    """Expone en Settings los umbrales definidos en res.company.
    No almacena datos propios: es una capa de UI sobre res_company.py,
    siguiendo el patrón estándar de res.config.settings en Odoo."""
    _inherit = 'res.config.settings'

    dashboard_ebitda_target = fields.Float(
        related='company_id.dashboard_ebitda_target', readonly=False,
        string='Objetivo de Margen EBITDA (%)',
    )
    dashboard_cash_runway_target_months = fields.Float(
        related='company_id.dashboard_cash_runway_target_months',
        readonly=False, string='Runway Objetivo (meses)',
    )
    dashboard_fx_method = fields.Selection(
        related='company_id.dashboard_fx_method', readonly=False,
        string='Método de Conversión FX',
    )
    dashboard_eliminate_intercompany = fields.Boolean(
        related='company_id.dashboard_eliminate_intercompany',
        readonly=False, string='Eliminar Transacciones Intercompañía',
    )
