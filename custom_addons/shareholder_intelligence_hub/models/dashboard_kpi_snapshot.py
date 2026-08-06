# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models



_logger = logging.getLogger(__name__)

# Tipos de cuenta (account_type) usados para clasificar sin mapeo manual.
# Ver Sección 3 del spec: account.account -> account_type.
REVENUE_TYPES = ('income', 'income_other')
COGS_TYPES = ('expense_direct_cost',)
OPEX_TYPES = ('expense',)
DA_TYPES = ('expense_depreciation',)
EQUITY_TYPES = ('equity', 'equity_unaffected')
ASSET_TYPES = (
    'asset_receivable', 'asset_cash', 'asset_current',
    'asset_non_current', 'asset_fixed', 'asset_prepayments',
)
CASH_TYPES = ('asset_cash',)
RECEIVABLE_TYPES = ('asset_receivable',)
PAYABLE_TYPES = ('liability_payable',)


class DashboardKpiSnapshot(models.Model):
    _name = 'dashboard.kpi.snapshot'
    _description = 'Executive Dashboard - KPI Snapshot'
    _order = 'snapshot_date desc, company_id'
    _rec_name = 'snapshot_date'

    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id', store=True, readonly=True,
    )
    snapshot_date = fields.Date(
        string='Fecha de Corte', required=True, index=True,
        default=fields.Date.context_today,
    )
    period_start = fields.Date(string='Inicio de Período (YTD)', required=True)
    period_end = fields.Date(string='Fin de Período', required=True)

    # ---------------------------------------------------------------
    # 4.1 KPIs de Cabecera
    # ---------------------------------------------------------------
    revenue_ytd = fields.Monetary(string='Ingresos Acumulados (YTD)')
    revenue_ytd_prev_year = fields.Monetary(string='Ingresos YTD Año Anterior')
    revenue_yoy_growth = fields.Float(string='Crecimiento YoY (%)')

    cogs = fields.Monetary(string='COGS')
    gross_margin = fields.Monetary(string='Margen Bruto')
    opex = fields.Monetary(string='OPEX (excl. D&A)')
    depreciation_amortization = fields.Monetary(string='D&A')
    ebitda = fields.Monetary(string='EBITDA')
    ebitda_margin = fields.Float(string='Margen EBITDA (%)')

    net_profit = fields.Monetary(string='Beneficio Neto')
    total_equity = fields.Monetary(string='Patrimonio Total')
    roe = fields.Float(string='ROE (%)')
    total_assets = fields.Monetary(string='Activo Total')
    roa = fields.Float(string='ROA (%)')

    cash_balance = fields.Monetary(string='Caja y Bancos')
    ar_total = fields.Monetary(string='Cuentas por Cobrar')
    ap_total = fields.Monetary(string='Cuentas por Pagar')
    cash_flow_available = fields.Monetary(string='Flujo de Caja Disponible')
    runway_months = fields.Float(string='Runway (meses)')

    # ---------------------------------------------------------------
    # 4.2 Antigüedad de Deuda (Aging) por tramos de días
    # ---------------------------------------------------------------
    ar_aging_0_30 = fields.Monetary(string='CxC 0-30 días')
    ar_aging_31_60 = fields.Monetary(string='CxC 31-60 días')
    ar_aging_61_90 = fields.Monetary(string='CxC 61-90 días')
    ar_aging_90_plus = fields.Monetary(string='CxC +90 días')

    ap_aging_0_30 = fields.Monetary(string='CxP 0-30 días')
    ap_aging_31_60 = fields.Monetary(string='CxP 31-60 días')
    ap_aging_61_90 = fields.Monetary(string='CxP 61-90 días')
    ap_aging_90_plus = fields.Monetary(string='CxP +90 días')

    computed_at = fields.Datetime(string='Calculado el', default=fields.Datetime.now)

    # Comparación contra el umbral configurable (ver models/res_company.py
    # y Settings vía models/dashboard_config.py).
    ebitda_target = fields.Float(
        related='company_id.dashboard_ebitda_target', readonly=True,
        string='Objetivo EBITDA (%)',
    )
    ebitda_margin_on_target = fields.Boolean(
        string='EBITDA cumple objetivo', compute='_compute_ebitda_on_target',
        store=True,
    )

    @api.depends('ebitda_margin', 'ebitda_target')
    def _compute_ebitda_on_target(self):
        for rec in self:
            rec.ebitda_margin_on_target = rec.ebitda_margin >= rec.ebitda_target

    """_sql_constraints = [
        (
            'company_date_uniq',
            'unique(company_id, snapshot_date)',
            'Ya existe un snapshot de KPIs para esta compañía en esta fecha.',
        ),
    ]"""

    _company_date_uniq = models.Constraint(
        'UNIQUE(company_id, snapshot_date)',
        'Ya existe un snapshot de KPIs para esta compañía en esta fecha.'
    )

    # ------------------------------------------------------------------
    # Punto de entrada del cron (ver data/ir_cron_data.xml)
    # ------------------------------------------------------------------
    @api.model
    def _cron_compute_kpi_snapshot(self):
        """Recalcula el snapshot del día para cada compañía activa.

        Este es el mecanismo que reemplaza la agregación en vivo sobre
        account.move.line en cada carga del dashboard (Sección 3.1.1).
        """
        companies = self.env['res.company'].search([])
        for company in companies:
            try:
                self._compute_kpis_for_company(company)
            except Exception:
                _logger.exception(
                    "Executive Dashboard: fallo calculando KPI snapshot "
                    "para la compañía '%s' (id=%s)", company.name, company.id,
                )

    def _compute_kpis_for_company(self, company):
        today = fields.Date.context_today(self)
        period_start = today.replace(month=1, day=1)  # Acumulado YTD

        vals = self._compute_kpi_values(company, period_start, today)

        existing = self.search([
            ('company_id', '=', company.id),
            ('snapshot_date', '=', today),
        ], limit=1)

        if existing:
            existing.write(vals)
        else:
            vals.update({
                'company_id': company.id,
                'snapshot_date': today,
                'period_start': period_start,
                'period_end': today,
            })
            self.create(vals)

    # ------------------------------------------------------------------
    # Cálculo de KPIs
    # ------------------------------------------------------------------
    def _compute_kpi_values(self, company, period_start, period_end):
        # Domain base: SIEMPRE filtrar asientos posteados (Sección 3.1.1).
        # Los borradores no deben contaminar cifras mostradas a la junta.
        flow_domain = [
            ('company_id', '=', company.id),
            ('move_id.state', '=', 'posted'),
            ('date', '>=', period_start),
            ('date', '<=', period_end),
        ]

        revenue = self._sum_by_account_type(flow_domain, REVENUE_TYPES)
        cogs = self._sum_by_account_type(flow_domain, COGS_TYPES)
        opex_total = self._sum_by_account_type(flow_domain, OPEX_TYPES)
        da = self._sum_by_account_type(flow_domain, DA_TYPES)
        opex_excl_da = opex_total - da

        gross_margin = revenue - cogs
        # EBITDA aislando D&A explícitamente (corrección Sección 4.3):
        # antes era un margen operativo (EBIT aprox.), no un EBITDA real.
        ebitda = gross_margin - opex_excl_da
        ebitda_margin = (ebitda / revenue * 100.0) if revenue else 0.0
        net_profit = revenue - cogs - opex_total

        # Domain de balance: saldo vivo a la fecha de corte (no acumulado
        # del período), para cuentas de activo/pasivo/patrimonio.
        balance_domain = [
            ('company_id', '=', company.id),
            ('move_id.state', '=', 'posted'),
            ('date', '<=', period_end),
        ]

        total_equity = self._sum_by_account_type(balance_domain, EQUITY_TYPES)
        total_assets = self._sum_by_account_type(balance_domain, ASSET_TYPES)
        cash_balance = self._sum_by_account_type(balance_domain, CASH_TYPES)
        ar_total = self._sum_by_account_type(balance_domain, RECEIVABLE_TYPES)
        ap_total = self._sum_by_account_type(balance_domain, PAYABLE_TYPES)

        roe = (net_profit / total_equity * 100.0) if total_equity else 0.0
        roa = (net_profit / total_assets * 100.0) if total_assets else 0.0

        cash_flow_available = cash_balance + ar_total - ap_total
        monthly_burn = (opex_excl_da / 12.0) if opex_excl_da else 0.0
        runway_months = (cash_balance / monthly_burn) if monthly_burn else 0.0

        ar_aging = self._compute_aging(company, period_end, RECEIVABLE_TYPES)
        ap_aging = self._compute_aging(company, period_end, PAYABLE_TYPES)

        return {
            'revenue_ytd': revenue,
            'cogs': cogs,
            'gross_margin': gross_margin,
            'opex': opex_excl_da,
            'depreciation_amortization': da,
            'ebitda': ebitda,
            'ebitda_margin': ebitda_margin,
            'net_profit': net_profit,
            'total_equity': total_equity,
            'roe': roe,
            'total_assets': total_assets,
            'roa': roa,
            'cash_balance': cash_balance,
            'ar_total': ar_total,
            'ap_total': ap_total,
            'cash_flow_available': cash_flow_available,
            'runway_months': runway_months,
            'ar_aging_0_30': ar_aging['0_30'],
            'ar_aging_31_60': ar_aging['31_60'],
            'ar_aging_61_90': ar_aging['61_90'],
            'ar_aging_90_plus': ar_aging['90_plus'],
            'ap_aging_0_30': ap_aging['0_30'],
            'ap_aging_31_60': ap_aging['31_60'],
            'ap_aging_61_90': ap_aging['61_90'],
            'ap_aging_90_plus': ap_aging['90_plus'],
            'computed_at': fields.Datetime.now(),
        }

    def _sum_by_account_type(self, domain, account_types):
        """Suma agregada (read_group) de account.move.line.balance,
        filtrando por account_type. Usa índices sobre company_id/date/
        account_type (Sección 3.1.1)."""
        full_domain = domain + [('account_id.account_type', 'in', list(account_types))]
        result = self.env['account.move.line'].read_group(
            full_domain, ['balance:sum'], [],
        )
        if result and result[0].get('balance'):
            return abs(result[0]['balance'])
        return 0.0

    def _compute_aging(self, company, as_of_date, account_types):
        """Antigüedad de saldos no conciliados, por tramos de días desde
        el vencimiento (date_maturity), para CxC/CxP (Sección 4.2)."""
        AccountMoveLine = self.env['account.move.line']
        domain = [
            ('company_id', '=', company.id),
            ('move_id.state', '=', 'posted'),
            ('account_id.account_type', 'in', list(account_types)),
            ('reconciled', '=', False),
            ('date_maturity', '!=', False),
        ]
        lines = AccountMoveLine.search(domain)
        buckets = {'0_30': 0.0, '31_60': 0.0, '61_90': 0.0, '90_plus': 0.0}
        for line in lines:
            days_overdue = (as_of_date - line.date_maturity).days
            amount = abs(line.amount_residual)
            if days_overdue <= 30:
                buckets['0_30'] += amount
            elif days_overdue <= 60:
                buckets['31_60'] += amount
            elif days_overdue <= 90:
                buckets['61_90'] += amount
            else:
                buckets['90_plus'] += amount
        return buckets
