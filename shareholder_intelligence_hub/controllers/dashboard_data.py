# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class DashboardDataController(http.Controller):

    @http.route('/shareholder_intelligence_hub/kpis', type='json', auth='user')
    def get_latest_kpis(self, company_id=None, **kw):
        # Conversión segura del ID de la compañía
        try:
            target_company_id = int(company_id) if company_id else request.env.company.id
        except (ValueError, TypeError):
            target_company_id = request.env.company.id

        allowed_company_ids = request.env.user.company_ids.ids
        if target_company_id not in allowed_company_ids:
            return {'found': False}

        company = request.env['res.company'].browse(target_company_id)
        if not company.exists():
            return {'found': False}

        snapshot = request.env['dashboard.kpi.snapshot'].search(
            [('company_id', '=', target_company_id)],
            order='snapshot_date desc',
            limit=1,
        )

        if not snapshot:
            return {'found': False}

        return {
            'found': True,
            'company_id': company.id,
            'company_name': company.name,
            'currency_symbol': company.currency_id.symbol or '',
            'snapshot_date': snapshot.snapshot_date.isoformat() if snapshot.snapshot_date else '',
            'kpis': {
                'revenue_ytd': snapshot.revenue_ytd,
                'revenue_yoy_growth': snapshot.revenue_yoy_growth,
                'ebitda': snapshot.ebitda,
                'ebitda_margin': snapshot.ebitda_margin,
                'ebitda_yoy_growth': snapshot.ebitda_yoy_growth,
                'ebitda_target': snapshot.ebitda_target,
                'ebitda_margin_on_target': snapshot.ebitda_margin_on_target,
                'roe': snapshot.roe,
                'roe_yoy_delta': snapshot.roe_yoy_delta,
                'roa': snapshot.roa,
                'cash_flow_available': snapshot.cash_flow_available,
                'cash_flow_yoy_growth': snapshot.cash_flow_yoy_growth,
                'runway_months': snapshot.runway_months,
            },
            'pnl_waterfall': {
                'revenue': snapshot.revenue_ytd,
                'cogs': -abs(snapshot.cogs or 0),
                'gross_margin': snapshot.gross_margin,
                'opex': -abs(snapshot.opex or 0),
                'ebitda': snapshot.ebitda,
            },
            'aging': {
                'receivable': [
                    snapshot.ar_aging_0_30,
                    snapshot.ar_aging_31_60,
                    snapshot.ar_aging_61_90,
                    snapshot.ar_aging_90_plus,
                ],
                'payable': [
                    snapshot.ap_aging_0_30,
                    snapshot.ap_aging_31_60,
                    snapshot.ap_aging_61_90,
                    snapshot.ap_aging_90_plus,
                ],
            },
        }

    @http.route('/shareholder_intelligence_hub/companies', type='json', auth='user')
    def get_allowed_companies(self, **kw):
        companies = request.env.user.company_ids
        return [{'id': c.id, 'name': c.name} for c in companies]