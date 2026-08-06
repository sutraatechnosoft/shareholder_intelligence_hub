# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class DashboardDataController(http.Controller):
    """Endpoints JSON que alimentan el componente OWL del frontend.

    Separar esta capa del frontend (Sección 8.1) permite reescribir la
    presentación para OWL 2 sin tocar modelos ni lógica de negocio.
    Todo el control de acceso se apoya en el ORM (ir.rule + ir.model.access
    definidos en security/), nunca se hace bypass con sudo() salvo que se
    documente explícitamente por qué.
    """

    @http.route('/shareholder_intelligence_hub/kpis', type='json', auth='user')
    def get_latest_kpis(self, company_id=None):
        Snapshot = request.env['dashboard.kpi.snapshot']

        domain = []
        if company_id:
            domain.append(('company_id', '=', int(company_id)))

        # No se usa sudo(): las reglas de ir.rule (dashboard_record_rules.xml)
        # ya limitan qué compañías puede ver este usuario.
        snapshot = Snapshot.search(domain, order='snapshot_date desc', limit=1)

        if not snapshot:
            return {'found': False}

        return {
            'found': True,
            'company_id': snapshot.company_id.id,
            'company_name': snapshot.company_id.name,
            'currency_symbol': snapshot.currency_id.symbol,
            'snapshot_date': snapshot.snapshot_date.isoformat(),
            'kpis': {
                'revenue_ytd': snapshot.revenue_ytd,
                'ebitda': snapshot.ebitda,
                'ebitda_margin': snapshot.ebitda_margin,
                'ebitda_target': snapshot.ebitda_target,
                'ebitda_margin_on_target': snapshot.ebitda_margin_on_target,
                'roe': snapshot.roe,
                'roa': snapshot.roa,
                'cash_flow_available': snapshot.cash_flow_available,
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
                'receivable': {
                    '0_30': snapshot.ar_aging_0_30,
                    '31_60': snapshot.ar_aging_31_60,
                    '61_90': snapshot.ar_aging_61_90,
                    '90_plus': snapshot.ar_aging_90_plus,
                },
                'payable': {
                    '0_30': snapshot.ap_aging_0_30,
                    '31_60': snapshot.ap_aging_31_60,
                    '61_90': snapshot.ap_aging_61_90,
                    '90_plus': snapshot.ap_aging_90_plus,
                },
            },
        }

    @http.route('/shareholder_intelligence_hub/companies', type='json', auth='user')
    def get_allowed_companies(self):
        """Compañías que el usuario actual puede seleccionar en el filtro
        multi-compañía del dashboard (Sección 6)."""
        companies = request.env.user.company_ids
        return [{'id': c.id, 'name': c.name} for c in companies]
