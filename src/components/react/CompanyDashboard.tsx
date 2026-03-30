import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface Ratios {
  pe?: number | null;
  pb?: number | null;
  ps?: number | null;
  evEbitda?: number | null;
  roe?: number | null;
  roa?: number | null;
  netMargin?: number | null;
  grossMargin?: number | null;
  ebitdaMargin?: number | null;
  currentRatio?: number | null;
  quickRatio?: number | null;
  cashRatio?: number | null;
  debtEquity?: number | null;
  leverageRatio?: number | null;
  financialDebtRatio?: number | null;
  netDebtEbitda?: number | null;
  earningsPerShare?: number | null;
  freeCashFlowYield?: number | null;
  revenueGrowthYoy?: number | null;
  netIncomeGrowthYoy?: number | null;
  ebitdaGrowthYoy?: number | null;
  equityGrowthYoy?: number | null;
}

interface Karne {
  karlilik: number;
  buyume: number;
  borcluluk: number;
  toplam: number;
}

interface BalanceSheet {
  equity: number[];
  currentLiabilities: number[];
  nonCurrentLiabilities: number[];
  totalAssets: number[];
}

interface Props {
  ratios: Ratios;
  karne: Karne | null;
  balanceSheet: BalanceSheet;
  marketCap: number;
  ticker: string;
}

function fmt(n: number | null | undefined, decimals = 2): string {
  if (n == null) return '-';
  return n.toLocaleString('tr-TR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtLarge(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '-';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e12) return `${sign}${(abs / 1e12).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} T`;
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} Mlr`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} Mln`;
  return `${sign}${abs.toLocaleString('tr-TR')}`;
}

function getGrowthColor(val: number | null | undefined): string {
  if (val == null) return 'text-gray-400';
  if (val > 0) return 'text-green-600 dark:text-green-400';
  if (val < 0) return 'text-red-600 dark:text-red-400';
  return 'text-gray-500';
}

function MultiplierCard({ label, value, suffix }: { label: string; value: number | null | undefined; suffix?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-3 text-center dark:border-gray-700 dark:bg-gray-800">
      <p className="text-[10px] font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
      <p className="mt-1 font-mono text-lg font-bold text-gray-900 dark:text-white">
        {value != null ? fmt(value) : '-'}
      </p>
      {suffix && <p className="text-[10px] text-gray-400">{suffix}</p>}
    </div>
  );
}

export default function CompanyDashboard({ ratios, karne, balanceSheet, marketCap, ticker }: Props) {
  // Son dönem bilanço verileri (son index)
  const lastIdx = balanceSheet.equity.length - 1;
  const equity = lastIdx >= 0 ? balanceSheet.equity[lastIdx] : 0;
  const shortTermDebt = lastIdx >= 0 ? balanceSheet.currentLiabilities[lastIdx] : 0;
  const longTermDebt = lastIdx >= 0 ? balanceSheet.nonCurrentLiabilities[lastIdx] : 0;

  // Kaynak dağılımı
  const total = equity + shortTermDebt + longTermDebt;
  const equityPct = total > 0 ? (equity / total * 100) : 0;
  const shortPct = total > 0 ? (shortTermDebt / total * 100) : 0;
  const longPct = total > 0 ? (longTermDebt / total * 100) : 0;

  const doughnutData = {
    labels: ['Özkaynaklar', 'Kısa Vadeli Yük.', 'Uzun Vadeli Yük.'],
    datasets: [{
      data: [equity, shortTermDebt, longTermDebt],
      backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
      borderWidth: 0,
      hoverOffset: 4,
    }],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '60%',
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (item: { label?: string; raw: unknown }) =>
            `${item.label}: ₺${fmtLarge(item.raw as number)}`,
        },
      },
    },
  };

  return (
    <div className="space-y-6">
      {/* Değerleme Çarpanları */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Değerleme Çarpanları</h3>
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
          <MultiplierCard label="F/K" value={ratios.pe} />
          <MultiplierCard label="PD/DD" value={ratios.pb} />
          <MultiplierCard label="F/S" value={ratios.ps} />
          <MultiplierCard label="FD/FAVÖK" value={ratios.evEbitda} />
          <MultiplierCard label="HBK" value={ratios.earningsPerShare} suffix="TL" />
          <MultiplierCard label="Piy. Değeri" value={marketCap / 1e9} suffix="Mlr TL" />
        </div>
      </div>

      {/* Karlılık + Büyüme + Likidite Özet */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Karlılık */}
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Karlılık</h4>
          <div className="space-y-2">
            {[
              { label: 'Brüt Marj', value: ratios.grossMargin },
              { label: 'FAVÖK Marjı', value: ratios.ebitdaMargin },
              { label: 'Net Marj', value: ratios.netMargin },
              { label: 'ROE', value: ratios.roe },
              { label: 'ROA', value: ratios.roa },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
                <span className={`font-mono text-xs font-semibold ${getGrowthColor(value)}`}>
                  {value != null ? `%${fmt(value)}` : '-'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Büyüme (YoY) */}
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Büyüme (YoY)</h4>
          <div className="space-y-2">
            {[
              { label: 'Gelir', value: ratios.revenueGrowthYoy },
              { label: 'Net Kar', value: ratios.netIncomeGrowthYoy },
              { label: 'FAVÖK', value: ratios.ebitdaGrowthYoy },
              { label: 'Özkaynak', value: ratios.equityGrowthYoy },
              { label: 'SNK Verimi', value: ratios.freeCashFlowYield },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
                <span className={`font-mono text-xs font-semibold ${getGrowthColor(value)}`}>
                  {value != null ? `%${fmt(value)}` : '-'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Finansal Yapı */}
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Finansal Yapı</h4>
          <div className="space-y-2">
            {[
              { label: 'Cari Oran', value: ratios.currentRatio, suffix: '' },
              { label: 'Likidite Oranı', value: ratios.quickRatio, suffix: '' },
              { label: 'Nakit Oran', value: ratios.cashRatio, suffix: '' },
              { label: 'Borç/Özkaynak', value: ratios.debtEquity, suffix: '' },
              { label: 'Net Borç/FAVÖK', value: ratios.netDebtEbitda, suffix: '' },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
                <span className="font-mono text-xs font-semibold text-gray-900 dark:text-gray-100">
                  {value != null ? fmt(value) : '-'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Kaynak Dağılımı */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Kaynak Dağılımı</h4>
          <div className="mx-auto h-[180px] w-[180px]">
            <Doughnut data={doughnutData} options={doughnutOptions} />
          </div>
          <div className="mt-3 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-sm bg-green-500" />
                Özkaynaklar
              </span>
              <span className="font-mono font-semibold text-gray-700 dark:text-gray-300">%{fmt(equityPct, 1)}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-sm bg-yellow-500" />
                Kısa Vadeli Yük.
              </span>
              <span className="font-mono font-semibold text-gray-700 dark:text-gray-300">%{fmt(shortPct, 1)}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-sm bg-red-500" />
                Uzun Vadeli Yük.
              </span>
              <span className="font-mono font-semibold text-gray-700 dark:text-gray-300">%{fmt(longPct, 1)}</span>
            </div>
          </div>
        </div>

        {/* Karne */}
        {karne && (
          <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Finansal Karne</h4>
            <div className="flex items-center justify-center py-4">
              <div className="text-center">
                <span className={`text-5xl font-bold ${
                  karne.toplam >= 14 ? 'text-green-500' :
                  karne.toplam >= 9 ? 'text-yellow-500' : 'text-red-500'
                }`}>
                  {karne.toplam}
                </span>
                <span className="text-xl text-gray-400">/18</span>
              </div>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Karlılık', score: karne.karlilik },
                { label: 'Büyüme', score: karne.buyume },
                { label: 'Borçluluk', score: karne.borcluluk },
              ].map(({ label, score }) => (
                <div key={label}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
                    <span className="text-xs font-bold text-gray-700 dark:text-gray-300">{score}/6</span>
                  </div>
                  <div className="flex gap-0.5">
                    {Array.from({ length: 6 }, (_, i) => (
                      <div
                        key={i}
                        className={`h-2 flex-1 rounded-sm ${
                          i < score
                            ? score >= 5 ? 'bg-green-500' : score >= 3 ? 'bg-yellow-500' : 'bg-red-500'
                            : 'bg-gray-200 dark:bg-gray-700'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
