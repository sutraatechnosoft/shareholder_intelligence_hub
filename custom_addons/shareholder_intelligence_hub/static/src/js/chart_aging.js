/** @odoo-module **/
import { Component, useRef, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ChartAging extends Component {
    static template = "shareholder_intelligence_hub.ChartAging";
    static props = {
        labels: { type: Array },
        values: { type: Array },
        title: { type: String },
        color: { type: String, optional: true },
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js").catch(() => {});
            this._renderChart();
        });
        onWillUpdateProps((nextProps) => this._updateChart(nextProps));
        onWillUnmount(() => this._destroyChart());
    }

    _renderChart() {
        const ChartLib = window.Chart;
        if (!ChartLib || !this.canvasRef.el) return;
        const ctx = this.canvasRef.el.getContext("2d");
        const defaultColors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545'];

        this.chart = new ChartLib(ctx, {
            type: 'bar',
            data: {
                labels: this.props.labels,
                datasets: [{
                    label: 'Monto ($)',
                    data: this.props.values,
                    backgroundColor: this.props.color ? [this.props.color, this.props.color, this.props.color, '#dc3545'] : defaultColors,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: this.props.title }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    _updateChart(nextProps) {
        if (this.chart) {
            this.chart.data.labels = nextProps.labels;
            this.chart.data.datasets[0].data = nextProps.values;
            this.chart.update();
        }
    }

    _destroyChart() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}
