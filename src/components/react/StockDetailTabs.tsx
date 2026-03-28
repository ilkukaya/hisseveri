import TabPanel from './TabPanel';
import FinancialTable from './FinancialTable';
import RevenueChart from './RevenueChart';
import RatioChart from './RatioChart';

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
}

interface Props {
  financials: FinancialData;
}

export default function StockDetailTabs({ financials }: Props) {
  if (!financials || !financials.periods || financials.periods.length === 0) {
    return (
      <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
        <p className="text-sm text-gray-400 dark:text-gray-500">Finansal veriler henüz mevcut değil</p>
      </div>
    );
  }

  // Check if all financial data is zeros
  const hasData = financials.incomeStatement.revenue.some((v) => v !== 0);
  if (!hasData) {
    return (
      <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
        <p className="text-sm text-gray-400 dark:text-gray-500">Finansal veriler henüz mevcut değil</p>
      </div>
    );
  }

  const { periods } = financials;

  const balanceSheetRows = [
    { label: 'Dönen Varlıklar', values: financials.balanceSheet.currentAssets },
    { label: 'Duran Varlıklar', values: financials.balanceSheet.nonCurrentAssets },
    { label: 'Toplam Varlıklar', values: financials.balanceSheet.totalAssets },
    { label: 'Kısa Vadeli Yükümlülükler', values: financials.balanceSheet.currentLiabilities },
    { label: 'Uzun Vadeli Yükümlülükler', values: financials.balanceSheet.nonCurrentLiabilities },
    { label: 'Toplam Yükümlülükler', values: financials.balanceSheet.totalLiabilities },
    { label: 'Özkaynaklar', values: financials.balanceSheet.equity },
  ];

  const incomeRows = [
    { label: 'Net Satışlar', values: financials.incomeStatement.revenue },
    { label: 'Satışların Maliyeti', values: financials.incomeStatement.costOfRevenue },
    { label: 'Brüt Kâr', values: financials.incomeStatement.grossProfit },
    { label: 'Faaliyet Kârı', values: financials.incomeStatement.operatingIncome },
    { label: 'Net Kâr', values: financials.incomeStatement.netIncome },
    { label: 'FAVÖK', values: financials.incomeStatement.ebitda },
  ];

  const cashFlowRows = [
    { label: 'İşletme Faaliyetlerinden', values: financials.cashFlow.operating },
    { label: 'Yatırım Faaliyetlerinden', values: financials.cashFlow.investing },
    { label: 'Finansman Faaliyetlerinden', values: financials.cashFlow.financing },
  ];

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

  return (
    <TabPanel
      tabs={[
        {
          label: 'Bilanço',
          content: <FinancialTable periods={periods} rows={balanceSheetRows} title="Bilanço" />,
        },
        {
          label: 'Gelir Tablosu',
          content: <FinancialTable periods={periods} rows={incomeRows} title="Gelir Tablosu" />,
        },
        {
          label: 'Nakit Akış',
          content: <FinancialTable periods={periods} rows={cashFlowRows} title="Nakit Akış Tablosu" />,
        },
        {
          label: 'Grafikler',
          content: (
            <div className="space-y-8">
              <div>
                <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                  Gelir ve Kâr Trendi
                </h3>
                <RevenueChart
                  periods={periods}
                  revenue={financials.incomeStatement.revenue}
                  netIncome={financials.incomeStatement.netIncome}
                />
              </div>
              <div>
                <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                  Karlılık Rasyoları Trendi
                </h3>
                <RatioChart
                  periods={periods}
                  series={[
                    { label: 'Brüt Kâr Marjı %', values: grossMarginSeries, color: '#3B82F6' },
                    { label: 'Net Kâr Marjı %', values: netMarginSeries, color: '#10B981' },
                  ]}
                />
              </div>
            </div>
          ),
        },
      ]}
    />
  );
}
