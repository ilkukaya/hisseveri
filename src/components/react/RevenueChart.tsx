import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

interface Props {
  periods: string[];
  revenue: number[];
  netIncome: number[];
}

function formatBillion(n: number): string {
  if (Math.abs(n) >= 1e9) return `${(n / 1e9).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} Mlr`;
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toLocaleString('tr-TR', { maximumFractionDigits: 0 })} Mln`;
  return n.toLocaleString('tr-TR');
}

export default function RevenueChart({ periods, revenue, netIncome }: Props) {
  const displayPeriods = [...periods].reverse();
  const displayRevenue = [...revenue].reverse();
  const displayNetIncome = [...netIncome].reverse();

  const data = {
    labels: displayPeriods,
    datasets: [
      {
        type: 'bar' as const,
        label: 'Net Satışlar',
        data: displayRevenue,
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: '#3B82F6',
        borderWidth: 1,
        yAxisID: 'y',
      },
      {
        type: 'line' as const,
        label: 'Net Kâr',
        data: displayNetIncome,
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2,
        pointRadius: 3,
        yAxisID: 'y',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: { color: '#9CA3AF', usePointStyle: true, pointStyle: 'circle' },
      },
      tooltip: {
        callbacks: {
          label: (item: { dataset: { label?: string }; raw: unknown }) =>
            `${item.dataset.label}: ₺${formatBillion(item.raw as number)}`,
        },
      },
    },
    scales: {
      x: { ticks: { color: '#9CA3AF' }, grid: { display: false } },
      y: {
        ticks: {
          color: '#9CA3AF',
          callback: (val: string | number) => formatBillion(Number(val)),
        },
        grid: { color: 'rgba(156, 163, 175, 0.15)' },
      },
    },
  };

  return (
    <div className="h-[300px] sm:h-[350px]">
      <Chart type="bar" data={data} options={options} />
    </div>
  );
}
