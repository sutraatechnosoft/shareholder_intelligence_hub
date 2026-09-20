# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

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
CREDIT_NATURED_TYPES = REVENUE_TYPES + EQUITY_TYPES + PAYABLE_TYPES


class DashboardKpiSnapshot(models.Model):
    _name = 'dashboard.kpi.snapshot'
    _description = 'KPIX Dashboard - KPI Snapshot'
    _order = 'snapshot_date desc, company_id'
    _rec_name = 'snapshot_date'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id', store=True, readonly=True,
    )
    snapshot_date = fields.Date(
        string='Snapshot Date', required=True, index=True,
        default=fields.Date.context_today,
    )
    period_start = fields.Date(string='Period Start (YTD)', required=True)
    period_end = fields.Date(string='Period End', required=True)

    # ---------------------------------------------------------------
    # 4.1 Header KPIs
    # ---------------------------------------------------------------
    revenue_ytd = fields.Monetary(string='YTD Revenue')
    revenue_ytd_prev_year = fields.Monetary(string='Previous Year YTD Revenue')
    revenue_yoy_growth = fields.Monetary(string='YoY Revenue Growth (%)')

    ebitda_prev_year = fields.Monetary(string='Previous Year EBITDA')
    ebitda_yoy_growth = fields.Monetary(string='YoY EBITDA Growth (%)')

    cash_flow_available_prev_year = fields.Monetary(string='Previous Year Cash Flow')
    cash_flow_yoy_growth = fields.Monetary(string='YoY Cash Flow Growth (%)')

    roe_prev_year = fields.Float(string='Previous Year ROE (%)')
    roe_yoy_delta = fields.Float(string='YoY ROE Change (pts)')

    cogs = fields.Monetary(string='COGS')
    gross_margin = fields.Monetary(string='Gross Margin')
    opex = fields.Monetary(string='OPEX (excl. D&A)')
    depreciation_amortization = fields.Monetary(string='D&A')
    ebitda = fields.Monetary(string='EBITDA')
    ebitda_margin = fields.Float(string='EBITDA Margin (%)')

    net_profit = fields.Monetary(string='Net Profit')
    total_equity = fields.Monetary(string='Total Equity')
    roe = fields.Float(string='ROE (%)')
    total_assets = fields.Monetary(string='Total Assets')
    roa = fields.Float(string='ROA (%)')

    cash_balance = fields.Monetary(string='Cash & Bank')
    ar_total = fields.Monetary(string='Accounts Receivable')
    ap_total = fields.Monetary(string='Accounts Payable')
    cash_flow_available = fields.Monetary(string='Available Cash Flow')
    runway_months = fields.Float(string='Runway (months)')

    # ---------------------------------------------------------------
    # 4.2 Debt Aging by day brackets
    # ---------------------------------------------------------------
    ar_aging_0_30 = fields.Monetary(string='AR 0-30 days')
    ar_aging_31_60 = fields.Monetary(string='AR 31-60 days')
    ar_aging_61_90 = fields.Monetary(string='AR 61-90 days')
    ar_aging_90_plus = fields.Monetary(string='AR 90+ days')

    ap_aging_0_30 = fields.Monetary(string='AP 0-30 days')
    ap_aging_31_60 = fields.Monetary(string='AP 31-60 days')
    ap_aging_61_90 = fields.Monetary(string='AP 61-90 days')
    ap_aging_90_plus = fields.Monetary(string='AP 90+ days')

    computed_at = fields.Datetime(string='Computed At', default=fields.Datetime.now)

    ebitda_target = fields.Float(
        related='company_id.dashboard_ebitda_target', readonly=True,
        string='EBITDA Target (%)',
    )
    ebitda_margin_on_target = fields.Boolean(
        string='EBITDA Meets Target', compute='_compute_ebitda_on_target',
        store=True,
    )

    @api.depends('ebitda_margin', 'ebitda_target')
    def _compute_ebitda_on_target(self):
        for rec in self:
            rec.ebitda_margin_on_target = rec.ebitda_margin >= rec.ebitda_target

    _company_date_uniq = models.Constraint(
        'UNIQUE(company_id, snapshot_date)',
        'A KPI snapshot for this company already exists on this date.'
    )

    # ------------------------------------------------------------------
    # AUTO-COMPUTE ON CREATE AND MANUAL BUTTON (NEW UI LOGIC)
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            snapshot_date = fields.Date.from_string(vals.get('snapshot_date')) or fields.Date.context_today(self)
            if not vals.get('period_start'):
                vals['period_start'] = snapshot_date.replace(month=1, day=1)
            if not vals.get('period_end'):
                vals['period_end'] = snapshot_date

        records = super().create(vals_list)
        records.action_recompute_kpis()
        return records

    def action_recompute_kpis(self):
        """Public method invoked by button in UI or after create"""
        for rec in self:
            p_start = rec.period_start or rec.snapshot_date.replace(month=1, day=1)
            p_end = rec.period_end or rec.snapshot_date
            vals = rec._compute_kpi_values(rec.company_id, p_start, p_end)
            rec.write(vals)
        return True

    # ------------------------------------------------------------------
    # Cron Entry Point
    # ------------------------------------------------------------------
    @api.model
    def _cron_compute_kpi_snapshot(self):
        companies = self.env['res.company'].search([])
        for company in companies:
            try:
                self._compute_kpis_for_company(company)
            except Exception:
                _logger.exception(
                    "KPIX Dashboard: failed computing KPI snapshot "
                    "for company '%s' (id=%s)", company.name, company.id,
                )

    def _compute_kpis_for_company(self, company):
        today = fields.Date.context_today(self)
        period_start = today.replace(month=1, day=1)

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
    # KPI Computation (Accounting Logic)
    # ------------------------------------------------------------------

    def _compute_kpi_values(self, company, period_start, period_end):
        flow_domain = [
            ('company_id', '=', company.id),
            ('move_id.state', '=', 'posted'),
            ('date', '>=', period_start),
            ('date', '<=', period_end),
        ]

        revenue = self._sum_by_account_type(flow_domain, REVENUE_TYPES)
        cogs = self._sum_by_account_type(flow_domain, COGS_TYPES)
        opex_excl_da = self._sum_by_account_type(flow_domain, OPEX_TYPES) 
        da = self._sum_by_account_type(flow_domain, DA_TYPES)             
        
        opex_total = opex_excl_da + da
        gross_margin = revenue - cogs
        ebitda = gross_margin - opex_excl_da
        ebitda_margin = (ebitda / revenue * 100.0) if revenue else 0.0
        
        # Net Profit must subtract COGS, OPEX and D&A
        net_profit = revenue - cogs - opex_total

        # ------------------------------------------------------------
        # YoY Revenue Growth (same period, previous year)
        # ------------------------------------------------------------
        try:
            prev_period_start = period_start.replace(year=period_start.year - 1)
        except ValueError:
            prev_period_start = period_start.replace(
                year=period_start.year - 1, day=28
            )
        try:
            prev_period_end = period_end.replace(year=period_end.year - 1)
        except ValueError:
            prev_period_end = period_end.replace(
                year=period_end.year - 1, day=28
            )

        prev_flow_domain = [
            ('company_id', '=', company.id),
            ('move_id.state', '=', 'posted'),
            ('date', '>=', prev_period_start),
            ('date', '<=', prev_period_end),
        ]
        revenue_prev_year = self._sum_by_account_type(prev_flow_domain, REVENUE_TYPES)
        revenue_yoy_growth = (
            ((revenue - revenue_prev_year) / revenue_prev_year) * 100.0
        ) if revenue_prev_year else 0.0

        cogs_prev_year = self._sum_by_account_type(prev_flow_domain, COGS_TYPES)
        opex_excl_da_prev_year = self._sum_by_account_type(prev_flow_domain, OPEX_TYPES)
        da_prev_year = self._sum_by_account_type(prev_flow_domain, DA_TYPES)
        opex_total_prev_year = opex_excl_da_prev_year + da_prev_year
        
        gross_margin_prev_year = revenue_prev_year - cogs_prev_year
        ebitda_prev_year = gross_margin_prev_year - opex_excl_da_prev_year
        ebitda_yoy_growth = (
            ((ebitda - ebitda_prev_year) / ebitda_prev_year) * 100.0
        ) if ebitda_prev_year else 0.0

        # ------------------------------------------------------------
        # Previous Year Balance Domain (at the same cutoff date)
        # ------------------------------------------------------------
        prev_balance_domain = [
            ('company_id', '=', company.id),
            ('move_id.state', '=', 'posted'),
            ('date', '<=', prev_period_end),
        ]

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
        
        elapsed_days = (period_end - period_start).days + 1
        elapsed_months = max(elapsed_days / 30.4375, 1.0)
        monthly_burn = (opex_excl_da / elapsed_months) if opex_excl_da else 0.0
        
        runway_months = (cash_balance / monthly_burn) if monthly_burn else 0.0

        # ------------------------------------------------------------
        # Available Cash Flow - Previous Year
        # ------------------------------------------------------------
        cash_balance_prev_year = self._sum_by_account_type(prev_balance_domain, CASH_TYPES)
        ar_total_prev_year = self._sum_by_account_type(prev_balance_domain, RECEIVABLE_TYPES)
        ap_total_prev_year = self._sum_by_account_type(prev_balance_domain, PAYABLE_TYPES)
        cash_flow_available_prev_year = (
            cash_balance_prev_year + ar_total_prev_year - ap_total_prev_year
        )
        cash_flow_yoy_growth = (
            ((cash_flow_available - cash_flow_available_prev_year)
             / cash_flow_available_prev_year) * 100.0
        ) if cash_flow_available_prev_year else 0.0

        # ------------------------------------------------------------
        # ROE - Previous Year (variation in percentage points)
        # ------------------------------------------------------------
        total_equity_prev_year = self._sum_by_account_type(prev_balance_domain, EQUITY_TYPES)
        net_profit_prev_year = revenue_prev_year - cogs_prev_year - opex_total_prev_year
        roe_prev_year = (
            (net_profit_prev_year / total_equity_prev_year * 100.0)
        ) if total_equity_prev_year else 0.0
        roe_yoy_delta = roe - roe_prev_year

        ar_aging = self._compute_aging(company, period_end, RECEIVABLE_TYPES)
        ap_aging = self._compute_aging(company, period_end, PAYABLE_TYPES)

        return {
            'revenue_ytd': revenue,
            'revenue_ytd_prev_year': revenue_prev_year,
            'revenue_yoy_growth': revenue_yoy_growth,
            'ebitda_prev_year': ebitda_prev_year,
            'ebitda_yoy_growth': ebitda_yoy_growth,
            'cash_flow_available_prev_year': cash_flow_available_prev_year,
            'cash_flow_yoy_growth': cash_flow_yoy_growth,
            'roe_prev_year': roe_prev_year,
            'roe_yoy_delta': roe_yoy_delta,
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
        full_domain = domain + [('account_id.account_type', 'in', list(account_types))]
        result = self.env['account.move.line']._read_group(
            full_domain, aggregates=['balance:sum'],
        )
        if not result:
            return 0.0

        balance = result[0][0] or 0.0

        if any(t in CREDIT_NATURED_TYPES for t in account_types):
            return -balance

        return balance




    def _compute_aging(self, company, as_of_date, account_types):
        buckets = {'0_30': 0.0, '31_60': 0.0, '61_90': 0.0, '90_plus': 0.0}
        for acc_type in account_types:
            domain = [
                ('company_id', '=', company.id),
                ('move_id.state', '=', 'posted'),
                ('account_id.account_type', '=', acc_type),
                ('reconciled', '=', False),
                ('date_maturity', '!=', False),
            ]
            data = self.env['account.move.line']._read_group(
                domain,
                groupby=['date_maturity'],
                aggregates=['amount_residual:sum'],
            )
            for date_maturity, amount_sum in data:
                if not date_maturity:
                    continue
                days = (as_of_date - date_maturity).days
                amount = abs(amount_sum or 0.0)
                if days <= 30:
                    buckets['0_30'] += amount
                elif days <= 60:
                    buckets['31_60'] += amount
                elif days <= 90:
                    buckets['61_90'] += amount
                else:
                    buckets['90_plus'] += amount
        return buckets