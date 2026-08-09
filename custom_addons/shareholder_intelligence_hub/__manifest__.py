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
    'author': 'Sutraa Technosoft',
    'website': 'https://tuempresa.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'web',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/dashboard_record_rules.xml',
        'data/ir_cron_data.xml',
        'views/dashboard_kpi_snapshot_views.xml',
        'views/dashboard_menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            # 1. Estilos primero
            'shareholder_intelligence_hub/static/src/scss/dashboard.scss',

            # 2. Plantillas XML (Cargadas ANTES del JS para que OWL reconozca los t-name)
            'shareholder_intelligence_hub/static/src/xml/dashboard_templates.xml',

            # 3. Componentes JS ordenados por dependencia
            'shareholder_intelligence_hub/static/src/js/kpi_card.js',
            'shareholder_intelligence_hub/static/src/js/chart_waterfall.js',
            'shareholder_intelligence_hub/static/src/js/chart_aging.js',
            'shareholder_intelligence_hub/static/src/js/dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}