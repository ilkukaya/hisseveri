import { Component, type ReactNode } from 'react';
import TabPanel from './TabPanel';
import FinancialTable from './FinancialTable';
import DetailedFinancialTable from './DetailedFinancialTable';
import RevenueChart from './RevenueChart';
import RatioChart from './RatioChart';
import QuarterlyBarChart from './QuarterlyBarChart';
import RatioAnalysisTable from './RatioAnalysisTable';
import CompanyDashboard from './CompanyDashboard';
import type { DetailedFinancialItem } from '../../utils/types';

class ChartErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) {
      return <div className="flex h-[200px] items-center justify-center text-sm text-gray-400">Grafik yüklenemedi</div>;
    }
    return this.props.children;
  }
}

interface FinancialData {
  periods: string[];
  balanceSheet: {
    currentAssets: number[];
    nonCurrentAssets: number[];
    totalAssets: number[];
    currentLiabilities: number[];
    nonCurrentLiabilities: number[];
    totalLiabilities: number[];
    equity: number[];
  };
  incomeStatement: {
    revenue: number[];
    costOfRevenue: number[];
    grossProfit: number[];
    operatingIncome: number[];
    netIncome: number[];
    ebitda: number[];
  };
  cashFlow: {
    operating: number[];
    investing: number[];
    financing: number[];
  };
  detailed?: {
    balanceSheet: DetailedFinancialItem[];
    incomeStatement: DetailedFinancialItem[];
    cashFlow: DetailedFinancialItem[];
  };
}

interface QuarterlyData {
  period: string;
  [key: string]: number | string | null | undefined;
}

interface Karne {
  karlilik: number;
  buyume: number;
  borcluluk: number;
  toplam: number;
}

interface Ratios {
  [key: string]: number | null | undefined;
}

interface Props {
  financials: FinancialData;
  quarterlyRatios?: QuarterlyData[];
  karne?: Karne | null;
  ratios?: Ratios;
  marketCap?: number;
  ticker?: string;
}

export default function StockDetailTabs({ financials, quarterlyRatios, karne, ratios, marketCap, ticker }: Props) {
  if (!financials || !financials.periods || financials.periods.length === 0) {
    return (
      <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
        <p className="text-sm text-gray-400 dark:text-gray-500">Finansal veriler henüz mevcut değil</p>
      </div>
    );
  }

  const hasData = financials.incomeStatement.revenue.some((v) => v !== 0);
  if (!hasData) {
    return (
      <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
        <p className="text-sm text-gray-400 dark:text-gray-500">Finansal veriler henüz mevcut değil</p>
      </div>
    );
  }

  const { periods } = financials;

  const hasDetailed = financials.detailed &&
    (financials.detailed.balanceSheet.length > 0 ||
     financials.detailed.incomeStatement.length > 0 ||
     financials.detailed.cashFlow.length > 0);

  const hasQuarterlyRatios = quarterlyRatios && quarterlyRatios.length > 0;

  const grossMarginSeries = financials.incomeStatement.grossProfit.map((gp, idx) =>
    financials.incomeStatement.revenue[idx] > 0
      ? Math.round((gp / financials.incomeStatement.revenue[idx]) * 10000) / 100
      : null,
  );

  const netMarginSeries = financials.incomeStatement.netIncome.map((ni, idx) =>
    financials.incomeStatement.revenue[idx] > 0
      ? Math.round((ni / financials.incomeStatement.revenue[idx]) * 10000) / 100
      : null,
  );

  const tabs = [];

  // 1. Özet Dashboard (eğer rasyo varsa)
  if (ratios && hasQuarterlyRatios) {
    tabs.push({
      label: 'Özet',
      content: (
        <ChartErrorBoundary>
          <CompanyDashboard
            ratios={ratios}
            karne={karne || null}
            balanceSheet={financials.balanceSheet}
            marketCap={marketCap || 0}
            ticker={ticker || ''}
          />
        </ChartErrorBoundary>
      ),
    });
  }

  // 2. Bilanço
  tabs.push({
    label: 'Bilanço',
    content: hasDetailed && financials.detailed!.balanceSheet.length > 0
      ? <DetailedFinancialTable periods={periods} items={financials.detailed!.balanceSheet} title="Bilanço" />
      : <FinancialTable periods={periods} rows={[
          { label: 'Dönen Varlıklar', values: financials.balanceSheet.currentAssets },
          { label: 'Duran Varlıklar', values: financials.balanceSheet.nonCurrentAssets },
          { label: 'Toplam Varlıklar', values: financials.balanceSheet.totalAssets },
          { label: 'Kısa Vadeli Yükümlülükler', values: financials.balanceSheet.currentLiabilities },
          { label: 'Uzun Vadeli Yükümlülükler', values: financials.balanceSheet.nonCurrentLiabilities },
          { label: 'Toplam Yükümlülükler', values: financials.balanceSheet.totalLiabilities },
          { label: 'Özkaynaklar', values: financials.balanceSheet.equity },
        ]} title="Bilanço" />,
  });

  // 3. Gelir Tablosu
  tabs.push({
    label: 'Gelir Tablosu',
    content: hasDetailed && financials.detailed!.incomeStatement.length > 0
      ? <DetailedFinancialTable periods={periods} items={financials.detailed!.incomeStatement} title="Gelir Tablosu" />
      : <FinancialTable periods={periods} rows={[
          { label: 'Net Satışlar', values: financials.incomeStatement.revenue },
          { label: 'Satışların Maliyeti', values: financials.incomeStatement.costOfRevenue },
          { label: 'Brüt Kâr', values: financials.incomeStatement.grossProfit },
          { label: 'Faaliyet Kârı', values: financials.incomeStatement.operatingIncome },
          { label: 'Net Kâr', values: financials.incomeStatement.netIncome },
          { label: 'FAVÖK', values: financials.incomeStatement.ebitda },
        ]} title="Gelir Tablosu" />,
  });

  // 4. Nakit Akış
  tabs.push({
    label: 'Nakit Akış',
    content: hasDetailed && financials.detailed!.cashFlow.length > 0
      ? <DetailedFinancialTable periods={periods} items={financials.detailed!.cashFlow} title="Nakit Akış Tablosu" />
      : <FinancialTable periods={periods} rows={[
          { label: 'İşletme Faaliyetlerinden', values: financials.cashFlow.operating },
          { label: 'Yatırım Faaliyetlerinden', values: financials.cashFlow.investing },
          { label: 'Finansman Faaliyetlerinden', values: financials.cashFlow.financing },
        ]} title="Nakit Akış Tablosu" />,
  });

  // 5. Rasyo Analizi
  if (hasQuarterlyRatios) {
    tabs.push({
      label: 'Rasyo Analizi',
      content: <RatioAnalysisTable quarterlyRatios={quarterlyRatios!} />,
    });
  }

  // 6. Grafikler
  tabs.push({
    label: 'Grafikler',
    content: (
      <ChartErrorBoundary>
        <div className="space-y-8">
          {/* Çeyreklik bar grafikler */}
          {hasQuarterlyRatios && (
            <>
              <QuarterlyBarChart
                data={quarterlyRatios!}
                series={[
                  { key: 'gelir', label: 'Gelir', color: '#3B82F6' },
                  { key: 'brutKar', label: 'Brüt Kar', color: '#10B981' },
                ]}
                title="Gelir ve Brüt Kar (Çeyreklik)"
              />
              <QuarterlyBarChart
                data={quarterlyRatios!}
                series={[
                  { key: 'favok', label: 'FAVÖK', color: '#8B5CF6' },
                  { key: 'netKar', label: 'Net Kar', color: '#F59E0B' },
                ]}
                title="FAVÖK ve Net Kar (Çeyreklik)"
              />
              <QuarterlyBarChart
                data={quarterlyRatios!}
                series={[
                  { key: 'isletmeNakitAkisi', label: 'İşletme Nakit Akışı', color: '#10B981' },
                  { key: 'serbestNakitAkis', label: 'Serbest Nakit Akış', color: '#3B82F6' },
                ]}
                title="Nakit Akış (Çeyreklik)"
              />
            </>
          )}

          {/* Klasik gelir-kar trendi (kümülatif) */}
          <div>
            <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
              Gelir ve Kâr Trendi (Kümülatif)
            </h3>
            <RevenueChart
              periods={periods}
              revenue={financials.incomeStatement.revenue}
              netIncome={financials.incomeStatement.netIncome}
            />
          </div>

          {/* Marj grafikleri */}
          {hasQuarterlyRatios && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Kar Marjları Trendi (Çeyreklik)
              </h3>
              <RatioChart
                periods={quarterlyRatios!.map(q => q.period as string)}
                series={[
                  { label: 'Brüt Kar Marjı %', values: quarterlyRatios!.map(q => q.brutKarMarji as number ?? null), color: '#3B82F6' },
                  { label: 'FAVÖK Marjı %', values: quarterlyRatios!.map(q => q.favokMarji as number ?? null), color: '#8B5CF6' },
                  { label: 'Net Kar Marjı %', values: quarterlyRatios!.map(q => q.netKarMarji as number ?? null), color: '#10B981' },
                ]}
                alreadyChronological
              />
            </div>
          )}

          {/* Likidite grafikleri */}
          {hasQuarterlyRatios && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Likidite Oranları Trendi
              </h3>
              <RatioChart
                periods={quarterlyRatios!.map(q => q.period as string)}
                series={[
                  { label: 'Cari Oran', values: quarterlyRatios!.map(q => q.cariOran as number ?? null), color: '#3B82F6' },
                  { label: 'Likidite Oranı', values: quarterlyRatios!.map(q => q.likiditeOrani as number ?? null), color: '#10B981' },
                  { label: 'Nakit Oran', values: quarterlyRatios!.map(q => q.nakitOran as number ?? null), color: '#F59E0B' },
                ]}
                alreadyChronological
              />
            </div>
          )}

          {/* Kaldıraç grafikleri */}
          {hasQuarterlyRatios && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Kaldıraç Oranları Trendi
              </h3>
              <RatioChart
                periods={quarterlyRatios!.map(q => q.period as string)}
                series={[
                  { label: 'Kaldıraç Oranı', values: quarterlyRatios!.map(q => q.kaldiracOrani as number ?? null), color: '#EF4444' },
                  { label: 'Finansal Borç Oranı', values: quarterlyRatios!.map(q => q.finansalBorcOrani as number ?? null), color: '#F59E0B' },
                ]}
                alreadyChronological
              />
            </div>
          )}

          {/* ROE/ROA */}
          {hasQuarterlyRatios && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Karlılık Oranları Trendi (TTM)
              </h3>
              <RatioChart
                periods={quarterlyRatios!.map(q => q.period as string)}
                series={[
                  { label: 'ROE %', values: quarterlyRatios!.map(q => q.roe as number ?? null), color: '#3B82F6' },
                  { label: 'ROA %', values: quarterlyRatios!.map(q => q.roa as number ?? null), color: '#10B981' },
                ]}
                alreadyChronological
              />
            </div>
          )}
        </div>
      </ChartErrorBoundary>
    ),
  });

  return <TabPanel tabs={tabs} />;
}
