/** @odoo-module **/

import { Component, useRef, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { user } from "@web/core/user";

export class ChartWaterfall extends Component {
    static template = "shareholder_intelligence_hub.ChartWaterfall";

    static props = {
        labels: Array,
        values: Array,
        isTotal: Array,  // marks bars that represent a running total
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(async () => {
            if (typeof window.Chart === "undefined") {
                await loadJS("/web/static/lib/Chart/Chart.js").catch(() => {});
            }
            this._renderChart();
        });

        onWillUpdateProps((nextProps) => this._renderChart(nextProps));

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
                this.chart = null;
            }
        });
    }

    _buildWaterfallData(labels, values, isTotalArr) {
        let runningTotal = 0;
        const floors = [];
        const bars = [];
        (values || []).forEach((v, index) => {
            const isTotal = !!(isTotalArr && isTotalArr[index]);
            if (isTotal) {
                floors.push(0);
                bars.push(Math.abs(v));
                runningTotal = v;
            } else {
                const start = runningTotal;
                const end = runningTotal + v;
                floors.push(Math.min(start, end));
                bars.push(Math.abs(v));
                runningTotal = end;
            }
        });
        return { floors, bars, isTotalFlags: isTotalArr || [] };
    }

    _renderChart(props) {
        const { labels, values, isTotal } = props || this.props;
        const ChartLib = window.Chart;
        if (!ChartLib || !this.canvasRef.el) {
            return;
        }
        const { floors, bars, isTotalFlags } = this._buildWaterfallData(labels, values, isTotal);

        if (this.chart) {
            this.chart.destroy();
        }

        const TOTAL_COLOR_RAMP = ["#5C6BC0", "#3949AB", "#1A237E"];
        let totalIndex = 0;

        const barColors = (values || []).map((v, i) => {
            if (isTotalFlags[i]) {
                const color = TOTAL_COLOR_RAMP[
                    Math.min(totalIndex, TOTAL_COLOR_RAMP.length - 1)
                ];
                totalIndex += 1;
                return color;
            }
            return v >= 0 ? "#2E7D32" : "#C62828"; 
        });

        // Detectar locale del usuario activo en Odoo
        const userLocale = user.lang ? user.lang.replace('_', '-') : undefined;

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
                        label: "Amount",
                        data: bars,
                        backgroundColor: barColors,
                        stack: "waterfall",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        filter: (item) => item.datasetIndex !== 0,
                        callbacks: {
                            label: (item) => {
                                const originalValue = (values || [])[item.dataIndex] ?? 0;
                                const sign = originalValue > 0 ? "+" : "";
                                return `${sign}${originalValue.toLocaleString(userLocale, {
                                    maximumFractionDigits: 0,
                                })}`;
                            },
                        },
                    },
                },
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