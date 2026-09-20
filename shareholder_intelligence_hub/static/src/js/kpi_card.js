/** @odoo-module **/

import { Component } from "@odoo/owl";

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