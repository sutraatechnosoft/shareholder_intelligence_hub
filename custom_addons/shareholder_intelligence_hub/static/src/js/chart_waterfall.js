/** @odoo-module **/

import { Component, useRef, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";

/**
 * Wrapper de Chart.js para el gráfico de cascada del Estado de Resultados
 * (Sección 4.2: "Estado de Resultados (P&L) — Waterfall Chart").
 *
 * Requiere que Chart.js esté cargado globalmente (window.Chart). Odoo trae
 * Chart.js empaquetado en /web/static/lib/Chart/Chart.js en varias
 * versiones; si tu build no lo incluye, agrégalo a la clave 'assets' del
 * manifest o cárgalo desde un CDN permitido.
 *
 * Chart.js no tiene un tipo "waterfall" nativo: se simula con un stacked
 * bar chart donde la primera serie es transparente (el "piso" de cada
 * barra) y la segunda es el valor visible.
 *
 * Props:
 *  - labels (Array<String>)  ej. ['Ingresos','COGS','Margen Bruto','OPEX','EBITDA']
 *  - values (Array<Number>)  deltas: positivos suman, negativos restan
 */
export class ChartWaterfall extends Component {
    static template = "shareholder_intelligence_hub.ChartWaterfall";
    static props = {
        labels: Array,
        values: Array,
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(() => this._renderChart());
        onWillUpdateProps((nextProps) => this._renderChart(nextProps));
        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    _buildWaterfallData(labels, values) {
        let cumulative = 0;
        const floors = [];
        const bars = [];
        for (const v of values) {
            const start = cumulative;
            const end = cumulative + v;
            floors.push(Math.min(start, end));
            bars.push(Math.abs(v));
            cumulative = end;
        }
        return { floors, bars };
    }

    _renderChart(props) {
        const { labels, values } = props || this.props;
        if (!window.Chart || !this.canvasRef.el) {
            return;
        }
        const { floors, bars } = this._buildWaterfallData(labels, values);

        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new window.Chart(this.canvasRef.el.getContext("2d"), {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "floor",
                        data: floors,
                        backgroundColor: "rgba(0,0,0,0)",
                        stack: "waterfall",
                    },
                    {
                        label: "valor",
                        data: bars,
                        backgroundColor: values.map((v) =>
                            v >= 0 ? "#2E7D32" : "#C62828"
                        ),
                        stack: "waterfall",
                    },
                ],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { stacked: true },
                    y: { stacked: true },
                },
            },
        });
    }
}
