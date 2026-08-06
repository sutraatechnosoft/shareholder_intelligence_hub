/** @odoo-module **/

import { Component } from "@odoo/owl";

/**
 * Tarjeta de KPI reutilizable (Sección 8: kpi_card.js).
 * Props:
 *  - title (String)
 *  - value (String)        ya formateado (moneda/porcentaje) por el padre
 *  - subtitle (String, opcional)
 *  - status ("good" | "warning" | "bad", opcional) — colorea el borde
 */
export class KpiCard extends Component {
    static template = "shareholder_intelligence_hub.KpiCard";
    static props = {
        title: String,
        value: String,
        subtitle: { type: String, optional: true },
        status: { type: String, optional: true },
    };
    static defaultProps = {
        subtitle: "",
        status: "neutral",
    };
}
