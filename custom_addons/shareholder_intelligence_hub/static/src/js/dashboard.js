/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { KpiCard } from "./kpi_card";
import { ChartWaterfall } from "./chart_waterfall";


export class ShareholderIntelligenceHubDashboard extends Component {
    static template = "shareholder_intelligence_hub.Dashboard";
    static components = { KpiCard, ChartWaterfall };

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
        if (result.found) {
            this.state.selectedCompanyId = result.company_id;
        }
        this.state.loading = false;
    }

    async onCompanyChange(ev) {
        const companyId = parseInt(ev.target.value, 10);
        await this._loadKpis(companyId);
    }

    // --- Helpers de formato usados en el template ---

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

    get waterfallLabels() {
        return ["Ingresos", "COGS", "Margen Bruto", "OPEX", "EBITDA"];
    }

    get waterfallValues() {
        const w = this.state.data?.pnl_waterfall;
        if (!w) return [];
        // Deltas relativos para el efecto cascada.
        return [w.revenue, w.cogs, 0, w.opex, 0];
    }
}

registry
    .category("actions")
    .add("shareholder_intelligence_hub.dashboard", ShareholderIntelligenceHubDashboard);
