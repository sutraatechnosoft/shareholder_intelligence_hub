# -*- coding: utf-8 -*-
{
    'name': 'Kpix Financial Dashboard',
    'version': '19.0.1.0.0',
    'summary': 'Board-ready financial dashboard with pre-calculated KPIs',
    'description': """
KPIX Dashboard
==============

Turn Odoo's accounting data into a board-ready financial dashboard
without recalculating large amounts of accounting data on every page load.

Key Features
------------
- Pre-calculated KPI snapshots.
- Revenue, gross margin, EBITDA, net profit, ROE and ROA.
- D&A properly isolated from OPEX for EBITDA calculation.
- Year-over-year comparisons.
- Accounts receivable and payable aging in 30-day brackets.
- Runway estimate based on current cash burn.
- Automatic KPI snapshots through scheduled actions.
- Configurable EBITDA and runway targets per company.
- Read-only Executive/Shareholder security group.
- Per-company record-level access.
- Optimized for large accounting datasets.

Performance
-----------
KPIs are pre-computed and stored in snapshot records rather than
being recalculated from account.move.line every time the dashboard
is opened.

Requirements
------------
Depends on the standard Odoo Account module.
No Enterprise dependency is required.
""",
    'author': 'Sutraa Technosoft',
    'website': 'https://sutraatechnosoft.com',
    'license': 'OPL-1',
    'category': 'Accounting/Accounting',

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
            'shareholder_intelligence_hub/static/src/scss/dashboard.scss',
            'shareholder_intelligence_hub/static/src/xml/dashboard_templates.xml',
            'shareholder_intelligence_hub/static/src/js/kpi_card.js',
            'shareholder_intelligence_hub/static/src/js/chart_waterfall.js',
            'shareholder_intelligence_hub/static/src/js/chart_aging.js',
            'shareholder_intelligence_hub/static/src/js/dashboard.js',
        ],
    },

    'images': [
        'static/description/banner.png',
    ],

    'price': 199.00,
    'currency': 'USD',
    'support': 'support@sutraatechnosoft.com',

    'installable': True,
    'application': True,
    'auto_install': False,
}