# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ------------------------------------------------------------------
    # Umbrales configurables (Sección 8: dashboard_config.py + res_company.py
    # trabajan juntos — los valores viven acá, la UI de Settings en
    # dashboard_config.py).
    # ------------------------------------------------------------------
    dashboard_ebitda_target = fields.Float(
        string='Objetivo de Margen EBITDA (%)', default=25.0,
        help='Umbral directivo de referencia. Ver Sección 4.1: '
             '"Objetivo directivo: > 25.0%".',
    )
    dashboard_cash_runway_target_months = fields.Float(
        string='Runway Objetivo (meses)', default=6.0,
    )

    # ------------------------------------------------------------------
    # Consolidación multi-compañía (Sección 6.1: método de conversión y
    # eliminaciones intercompañía deben quedar explícitos, no implícitos).
    # ------------------------------------------------------------------
    dashboard_fx_method = fields.Selection(
        selection=[
            ('closing', 'Tipo de cambio de cierre'),
            ('average', 'Tipo de cambio promedio del período'),
        ],
        string='Método de Conversión FX', default='closing',
        help='Método usado al consolidar filiales con moneda distinta a '
             'la moneda corporativa. Ver Sección 6.1.',
    )
    dashboard_eliminate_intercompany = fields.Boolean(
        string='Eliminar Transacciones Intercompañía',
        default=True,
        help='Si está activo, las ventas/compras entre filiales del mismo '
             'grupo se excluyen del consolidado para no inflar el ingreso '
             'artificialmente (Sección 6.1).',
    )
