# controllers/dashboard_data.py
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import datetime

class DashboardDataController(http.Controller):

    @http.route('/shareholder_intelligence_hub/kpis', type='jsonrpc', auth='user')
    def get_latest_kpis(self, company_id=None):
        company_id = int(company_id) if company_id else request.env.company.id
        company = request.env['res.company'].browse(company_id)

        Snapshot = request.env['dashboard.kpi.snapshot']
        snapshot = Snapshot.search(
            [('company_id', '=', company_id)],
            order='snapshot_date desc', limit=1,
        )

        if not snapshot:
            return {'found': False}

        return {
            'found': True,
            'company_id': company.id,
            'company_name': company.name,
            'currency_symbol': company.currency_id.symbol,
            'snapshot_date': snapshot.snapshot_date.isoformat(),
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
                'cogs': -snapshot.cogs,
                'gross_margin': snapshot.gross_margin,
                'opex': -snapshot.opex,
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

    @http.route('/shareholder_intelligence_hub/companies', type='jsonrpc', auth='user')
    def get_allowed_companies(self):
        companies = request.env.user.company_ids
        return [{'id': c.id, 'name': c.name} for c in companies]