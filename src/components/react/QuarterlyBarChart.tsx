import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface QuarterlyData {
  period: string;
  [key: string]: number | string | null | undefined;
}

interface SeriesConfig {
  key: string;
  label: string;
  color: string;
}

interface Props {
  data: QuarterlyData[];
  series: SeriesConfig[];
  title?: string;
  formatValue?: (n: number) => string;
}

function defaultFormat(n: number): string {
  if (Math.abs(n) >= 1e9) return `${(n / 1e9).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} Mlr`;
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toLocaleString('tr-TR', { maximumFractionDigits: 0 })} Mln`;
  return n.toLocaleString('tr-TR');
}

export default function QuarterlyBarChart({ data, series, title, formatValue }: Props) {
  const fmt = formatValue || defaultFormat;

  const chartData = {
    labels: data.map((d) => d.period),
    datasets: series.map((s) => ({
      label: s.label,
      data: data.map((d) => (d[s.key] as number) ?? null),
      backgroundColor: s.color + 'B3', // ~70% opacity
      borderColor: s.color,
      borderWidth: 1,
      borderRadius: 3,
    })),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: { color: '#9CA3AF', usePointStyle: true, pointStyle: 'circle', font: { size: 11 } },
      },
      tooltip: {
        callbacks: {
          label: (item: { dataset: { label?: string }; raw: unknown }) =>
            `${item.dataset.label}: ₺${fmt(item.raw as number)}`,
        },
      },
    },
    scales: {
      x: { ticks: { color: '#9CA3AF', font: { size: 10 } }, grid: { display: false } },
      y: {
        ticks: { color: '#9CA3AF', callback: (val: string | number) => fmt(Number(val)) },
        grid: { color: 'rgba(156, 163, 175, 0.15)' },
      },
    },
  };

  return (
    <div>
      {title && <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{title}</h3>}
      <div className="h-[260px] sm:h-[300px]">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}
