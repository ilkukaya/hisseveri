import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface RatioSeries {
  label: string;
  values: (number | null)[];
  color: string;
}

interface Props {
  periods: string[];
  series: RatioSeries[];
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export default function RatioChart({ periods, series }: Props) {
  const displayPeriods = [...periods].reverse();

  const data = {
    labels: displayPeriods,
    datasets: series.map((s, i) => ({
      label: s.label,
      data: [...s.values].reverse(),
      borderColor: s.color || COLORS[i % COLORS.length],
      backgroundColor: 'transparent',
      borderWidth: 2,
      pointRadius: 3,
      tension: 0.3,
    })),
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
          label: (item: { dataset: { label?: string }; raw: unknown }) => {
            const val = item.raw as number | null;
            return `${item.dataset.label}: ${val != null ? val.toLocaleString('tr-TR', { minimumFractionDigits: 2 }) : '-'}`;
          },
        },
      },
    },
    scales: {
      x: { ticks: { color: '#9CA3AF' }, grid: { display: false } },
      y: {
        ticks: { color: '#9CA3AF' },
        grid: { color: 'rgba(156, 163, 175, 0.15)' },
      },
    },
  };

  return (
    <div className="h-[300px] sm:h-[350px]">
      <Line data={data} options={options} />
    </div>
  );
}
