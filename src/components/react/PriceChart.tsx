import { useState, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

interface PricePoint {
  date: string;
  close: number;
  volume: number;
}

interface Props {
  prices: PricePoint[];
  ticker: string;
}

type Period = '1A' | '3A' | '6A' | '1Y' | 'Tümü';

const PERIODS: { label: Period; days: number }[] = [
  { label: '1A', days: 22 },
  { label: '3A', days: 66 },
  { label: '6A', days: 132 },
  { label: '1Y', days: 252 },
  { label: 'Tümü', days: 9999 },
];

export default function PriceChart({ prices, ticker }: Props) {
  const [period, setPeriod] = useState<Period>('1Y');

  if (!prices || prices.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
        <p className="text-sm text-gray-400 dark:text-gray-500">Fiyat verisi henüz mevcut değil</p>
      </div>
    );
  }

  const filteredPrices = useMemo(() => {
    const days = PERIODS.find((p) => p.label === period)?.days || 9999;
    return prices.slice(-days);
  }, [prices, period]);

  const isPositive = filteredPrices.length >= 2 && filteredPrices[filteredPrices.length - 1].close >= filteredPrices[0].close;
  const lineColor = isPositive ? '#10B981' : '#EF4444';
  const bgColor = isPositive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';

  const data = {
    labels: filteredPrices.map((p) => {
      const d = new Date(p.date);
      return d.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' });
    }),
    datasets: [
      {
        data: filteredPrices.map((p) => p.close),
        borderColor: lineColor,
        backgroundColor: bgColor,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        fill: true,
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items: { dataIndex: number }[]) => {
            const idx = items[0]?.dataIndex;
            if (idx == null) return '';
            const p = filteredPrices[idx];
            return new Date(p.date).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });
          },
          label: (item: { raw: unknown }) => {
            const val = item.raw as number;
            return `${ticker}: ₺${val.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        ticks: { maxTicksLimit: 8, color: '#9CA3AF' },
        grid: { display: false },
      },
      y: {
        display: true,
        ticks: {
          color: '#9CA3AF',
          callback: (val: string | number) =>
            `₺${Number(val).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}`,
        },
        grid: { color: 'rgba(156, 163, 175, 0.15)' },
      },
    },
  };

  return (
    <div>
      <div className="mb-3 flex gap-1">
        {PERIODS.map((p) => (
          <button
            key={p.label}
            onClick={() => setPeriod(p.label)}
            className={`rounded px-3 py-1 text-xs font-medium transition ${
              period === p.label
                ? 'bg-accent text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="h-[300px] sm:h-[350px]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
