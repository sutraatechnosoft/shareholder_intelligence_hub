/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { KpiCard } from "@shareholder_intelligence_hub/js/kpi_card";
import { ChartWaterfall } from "@shareholder_intelligence_hub/js/chart_waterfall";
import { ChartAging } from "@shareholder_intelligence_hub/js/chart_aging";

export class ShareholderIntelligenceHubDashboard extends Component {
    static template = "shareholder_intelligence_hub.Dashboard";
    static components = { KpiCard, ChartWaterfall, ChartAging };

    setup() {
        this.state = useState({
            loading: true,
            found: false,
            data: null,
            companies: [],
            selectedCompanyId: null,
        });
        onWillStart(async () => {
            await this._loadCompanies();
            await this._loadKpis();
        });
    }

    async _loadCompanies() {
        this.state.companies = await rpc(
            "/shareholder_intelligence_hub/companies"
        );
    }

    async _loadKpis(companyId) {
        this.state.loading = true;
        const result = await rpc("/shareholder_intelligence_hub/kpis", {
            company_id: companyId || null,
        });
        this.state.found = result.found;
        this.state.data = result.found ? result : null;
        
        this.state.selectedCompanyId = companyId || result.company_id || null;

        this.state.loading = false;
    }
    

    async onCompanyChange(ev) {
        const companyId = parseInt(ev.target.value, 10);
        await this._loadKpis(companyId);
    }

    formatCurrency(value) {
        if (value === undefined || value === null) return "-";
        const symbol = this.state.data?.currency_symbol || "";
        return `${symbol} ${value.toLocaleString("es-ES", {
            maximumFractionDigits: 0,
        })}`;
    }

    formatPercent(value) {
        if (value === undefined || value === null) return "-";
        return `${value.toFixed(1)}%`;
    }

    formatYoY(value) {
        if (value === undefined || value === null) return "YoY: -";
        const sign = value >= 0 ? "+" : "";
        return `YoY: ${sign}${value.toFixed(1)}% vs prior year`;
    }

    formatYoYPoints(value) {
        if (value === undefined || value === null) return "YoY: -";
        const sign = value >= 0 ? "+" : "";
        return `YoY: ${sign}${value.toFixed(1)}% vs prior year`;
    }

    get waterfallLabels() {
        return ["Revenue", "COGS", "Gross Margin", "OPEX", "EBITDA"];
    }

    get waterfallValues() {
        const w = this.state.data?.pnl_waterfall;
        if (!w) return [];
        return [w.revenue, w.cogs, w.gross_margin, w.opex, w.ebitda];
    }
    get waterfallIsTotal() {
        return [true, false, true, false, true];  
    }

    get agingLabels() {
        return ["0-30 days", "31-60 days", "61-90 days", "+90 days"];
    }

    get arAgingValues() {
        return this.state.data?.aging?.receivable || [0, 0, 0, 0];
    }

    get apAgingValues() {
        return this.state.data?.aging?.payable || [0, 0, 0, 0];
    }
}

registry
    .category("actions")
    .add("shareholder_intelligence_hub.dashboard", ShareholderIntelligenceHubDashboard);