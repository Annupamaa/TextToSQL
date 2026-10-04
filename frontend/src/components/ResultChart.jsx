import { Bar, Line, Pie } from "react-chartjs-2";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend);

const COLORS = ["#2a6f97", "#e9a23b", "#3d9970", "#b5546b", "#6b5ca5", "#5b8a9a", "#c76d3a", "#7a8b3c"];
const MAX_POINTS = 100;
const CHARTS = { bar: Bar, line: Line, pie: Pie };

const isNumericColumn = (rows, i) =>
  rows.length > 0 && rows.every((r) => r[i] === null || (typeof r[i] === "number" && Number.isFinite(r[i])));

export function canChart(columns, rows) {
  return columns.length >= 2 && rows.length > 0 && columns.some((_, i) => i > 0 && isNumericColumn(rows, i));
}

export default function ResultChart({ type, columns, rows }) {
  const shown = rows.slice(0, MAX_POINTS);
  const numeric = columns.map((_, i) => i).filter((i) => i > 0 && isNumericColumn(shown, i));
  const Chart = CHARTS[type];
  if (!Chart || numeric.length === 0) return null;

  const datasets = numeric.map((col, k) => ({
    label: columns[col],
    data: shown.map((r) => r[col]),
    backgroundColor: type === "pie" ? shown.map((_, j) => COLORS[j % COLORS.length]) : COLORS[k % COLORS.length],
    borderColor: COLORS[k % COLORS.length],
    tension: 0.3,
  }));

  const data = {
    labels: shown.map((r) => String(r[0] ?? "NULL")),
    datasets: type === "pie" ? [datasets[0]] : datasets,
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: type === "pie" || datasets.length > 1 } },
  };

  return (
    <div className="chart-wrap">
      <Chart data={data} options={options} />
      {rows.length > MAX_POINTS && <p className="muted">Chart shows the first {MAX_POINTS} rows.</p>}
    </div>
  );
}
