# -*- coding: utf-8 -*-
{
    'name': 'Shareholder Intelligence Hub',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': (
        'Dashboard ejecutivo de KPIs financieros (EBITDA, ROE, ROA, aging, '
        'cash flow) para junta directiva y accionistas'
    ),
    'description': """
Shareholder Intelligence Hub
=============================

Consolida el motor contable de Odoo (account.move.line, account.move,
account.account) en un modelo de reporting precalculado
(dashboard.kpi.snapshot), evitando agregaciones en vivo sobre el ledger
en cada carga de pantalla (ver Seccion 3.1.1 de la especificacion tecnica).

Reglas de negocio clave implementadas:
- Todas las queries de KPIs filtran obligatoriamente state = 'posted'.
- EBITDA se calcula aislando D&A (depreciacion y amortizacion) del resto
  del OPEX, en vez de un margen operativo aproximado (Seccion 4.3).
- Snapshot horario/diario via cron (ir.cron) por compania, con indices
  sobre company_id, date y account_type.
- Umbrales configurables por compania (objetivo EBITDA, runway objetivo)
  expuestos en Settings (Seccion 4.1 / 8).
- Seguridad granular: grupo Executive/Shareholder de solo lectura +
  ir.rule por compania a nivel de registro, no solo de menu (Seccion 6.2).

Depende unicamente del modulo 'account' (Community), para no atarse a
funcionalidades Enterprise. Ver Seccion 2 del spec para la estrategia de
compatibilidad multi-version (v15-v18).
    """,
    'author': 'Tu Empresa',
    'website': 'https://tuempresa.com',
    'license': 'LGPL-3',
    # Dependencia deliberadamente minima: solo 'account' (Community).
    # No se depende de 'account_reports' ni otros modulos Enterprise.
    'depends': [
        'account',
        'web',
    ],
    'data': [
        # Seguridad primero: grupos antes que ir.model.access.csv (que los
        # referencia) y antes que las vistas/menus (que los usan en groups=).
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/dashboard_record_rules.xml',
        'data/ir_cron_data.xml',
        'views/dashboard_kpi_snapshot_views.xml',
        'views/dashboard_menus.xml',
    ],
    # Assets para Odoo 17/18 (OWL 2). Para v15/v16 ver la nota de
    # compatibilidad en views/dashboard_templates.xml.
    'assets': {
        'web.assets_backend': [
            'shareholder_intelligence_hub/static/src/js/kpi_card.js',
            'shareholder_intelligence_hub/static/src/js/chart_waterfall.js',
            'shareholder_intelligence_hub/static/src/js/dashboard.js',
            'shareholder_intelligence_hub/static/src/xml/dashboard_templates.xml',
            'shareholder_intelligence_hub/static/src/scss/dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}