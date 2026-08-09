/** @odoo-module **/

import { Component, useRef, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ChartWaterfall extends Component {
    static template = "shareholder_intelligence_hub.ChartWaterfall";
    static props = {
        labels: Array,
        values: Array,
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js").catch(() => {});
            this._renderChart();
        });

        onWillUpdateProps((nextProps) => this._renderChart(nextProps));

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    _buildWaterfallData(labels, values) {
        let runningTotal = 0;
        const floors = [];
        const bars = [];
        const isTotalFlags = [];

        (values || []).forEach((v, index) => {
            const label = (labels && labels[index]) ? labels[index].toLowerCase() : "";
            
            // Detecta si es una columna de subtotal/total
            const isTotal = label.includes("margen bruto") || label.includes("ebitda");
            isTotalFlags.push(isTotal);

            if (isTotal) {
                // Las barras de total nacen en 0 y suben hasta su valor real
                floors.push(0);
                bars.push(Math.abs(v));
                runningTotal = v;
            } else {
                // Las barras de variación (COGS/OPEX) flotan desde el acumulado anterior
                const start = runningTotal;
                const end = runningTotal + v;
                floors.push(Math.min(start, end));
                bars.push(Math.abs(v));
                runningTotal = end;
            }
        });

        return { floors, bars, isTotalFlags };
    }

    _renderChart(props) {
        const { labels, values } = props || this.props;
        const ChartLib = window.Chart;

        if (!ChartLib || !this.canvasRef.el) {
            return;
        }

        const { floors, bars, isTotalFlags } = this._buildWaterfallData(labels, values);

        if (this.chart) {
            this.chart.destroy();
        }

        // Asignación de colores: Azul/Gris para totales, Verde para aumentos, Rojo para costos/gastos
        const barColors = (values || []).map((v, i) => {
            if (isTotalFlags[i]) {
                return "#1E88E5"; // Azul para destacar subtotales y totales (Margen Bruto y EBITDA)
            }
            return v >= 0 ? "#2E7D32" : "#C62828"; // Verde para ingresos/positivos, Rojo para egresos
        });

        this.chart = new ChartLib(this.canvasRef.el.getContext("2d"), {
            type: "bar",
            data: {
                labels: labels || [],
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
                        backgroundColor: barColors,
                        stack: "waterfall",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { stacked: true },
                    y: { 
                        stacked: true,
                        beginAtZero: true
                    },
                },
            },
        });
    }
}