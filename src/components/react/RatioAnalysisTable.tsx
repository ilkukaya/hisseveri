import { useState } from 'react';

interface QuarterlyData {
  period: string;
  [key: string]: number | string | null | undefined;
}

interface RatioRow {
  key: string;
  label: string;
  format?: 'percent' | 'number' | 'ratio' | 'times';
}

interface RatioCategory {
  title: string;
  rows: RatioRow[];
}

interface Props {
  quarterlyRatios: QuarterlyData[];
}

const CATEGORIES: RatioCategory[] = [
  {
    title: 'Karlılık Oranları',
    rows: [
      { key: 'brutKarMarji', label: 'Brüt Kar Marjı', format: 'percent' },
      { key: 'favokMarji', label: 'FAVÖK Marjı', format: 'percent' },
      { key: 'esasFaaliyetKarMarji', label: 'Esas Faaliyet Kar Marjı', format: 'percent' },
      { key: 'netKarMarji', label: 'Net Kar Marjı', format: 'percent' },
      { key: 'roe', label: 'ROE (TTM)', format: 'percent' },
      { key: 'roa', label: 'ROA (TTM)', format: 'percent' },
      { key: 'hisseBasiKar', label: 'Hisse Başı Kar (TTM)', format: 'number' },
    ],
  },
  {
    title: 'Likidite Oranları',
    rows: [
      { key: 'cariOran', label: 'Cari Oran', format: 'ratio' },
      { key: 'likiditeOrani', label: 'Likidite (Asit-Test) Oranı', format: 'ratio' },
      { key: 'nakitOran', label: 'Nakit Oran', format: 'ratio' },
    ],
  },
  {
    title: 'Kaldıraç Oranları',
    rows: [
      { key: 'borcOzkaynak', label: 'Borç / Özkaynak', format: 'ratio' },
      { key: 'kaldiracOrani', label: 'Kaldıraç Oranı', format: 'ratio' },
      { key: 'finansalBorcOrani', label: 'Finansal Borç Oranı', format: 'ratio' },
      { key: 'netBorcFavok', label: 'Net Borç / FAVÖK (TTM)', format: 'ratio' },
    ],
  },
  {
    title: 'Faaliyet Etkinlik Oranları',
    rows: [
      { key: 'aktifDevirHizi', label: 'Aktif Devir Hızı (TTM)', format: 'times' },
      { key: 'stokDevirHizi', label: 'Stok Devir Hızı (TTM)', format: 'times' },
      { key: 'alacakDevirHizi', label: 'Alacak Devir Hızı (TTM)', format: 'times' },
      { key: 'borcDevirHizi', label: 'Borç Devir Hızı (TTM)', format: 'times' },
      { key: 'ozkaynakDevirHizi', label: 'Özkaynak Devir Hızı (TTM)', format: 'times' },
    ],
  },
  {
    title: 'Büyüme Oranları (YoY)',
    rows: [
      { key: 'gelirBuyumeYoy', label: 'Gelir Büyümesi', format: 'percent' },
      { key: 'netKarBuyumeYoy', label: 'Net Kar Büyümesi', format: 'percent' },
      { key: 'favokBuyumeYoy', label: 'FAVÖK Büyümesi', format: 'percent' },
      { key: 'ozkaynakBuyumeYoy', label: 'Özkaynak Büyümesi', format: 'percent' },
    ],
  },
  {
    title: 'Büyüme Oranları (QoQ)',
    rows: [
      { key: 'gelirBuyumeQoq', label: 'Gelir Büyümesi', format: 'percent' },
      { key: 'netKarBuyumeQoq', label: 'Net Kar Büyümesi', format: 'percent' },
      { key: 'favokBuyumeQoq', label: 'FAVÖK Büyümesi', format: 'percent' },
    ],
  },
];

function formatValue(val: number | null | undefined, format: string): string {
  if (val == null) return '-';
  switch (format) {
    case 'percent':
      return `%${val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    case 'ratio':
      return val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    case 'times':
      return `${val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}x`;
    case 'number':
      return val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
    default:
      return String(val);
  }
}

function getGrowthColor(val: number | null | undefined): string {
  if (val == null) return '';
  if (val > 0) return 'text-green-600 dark:text-green-400';
  if (val < 0) return 'text-red-600 dark:text-red-400';
  return '';
}

export default function RatioAnalysisTable({ quarterlyRatios }: Props) {
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>(
    Object.fromEntries(CATEGORIES.map((c) => [c.title, true]))
  );

  if (!quarterlyRatios || quarterlyRatios.length === 0) {
    return (
      <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
        <p className="text-sm text-gray-400">Rasyo verisi mevcut değil</p>
      </div>
    );
  }

  const toggleCategory = (title: string) => {
    setExpandedCategories((prev) => ({ ...prev, [title]: !prev[title] }));
  };

  return (
    <div className="space-y-4">
      {CATEGORIES.map((category) => (
        <div key={category.title} className="rounded-lg border border-gray-200 dark:border-gray-700">
          <button
            onClick={() => toggleCategory(category.title)}
            className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {category.title}
            </h3>
            <svg
              className={`h-4 w-4 text-gray-400 transition-transform ${
                expandedCategories[category.title] ? 'rotate-180' : ''
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {expandedCategories[category.title] && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-t border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
                    <th className="sticky left-0 z-10 bg-gray-50 px-4 py-2 text-left text-xs font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                      Oran
                    </th>
                    {quarterlyRatios.map((q) => (
                      <th
                        key={q.period as string}
                        className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400"
                      >
                        {q.period as string}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {category.rows.map((row, rowIdx) => (
                    <tr
                      key={row.key}
                      className={`border-t border-gray-100 dark:border-gray-800 ${
                        rowIdx % 2 === 0 ? '' : 'bg-gray-50/50 dark:bg-gray-800/30'
                      }`}
                    >
                      <td className="sticky left-0 z-10 whitespace-nowrap bg-white px-4 py-2 text-xs font-medium text-gray-700 dark:bg-gray-900 dark:text-gray-300">
                        {row.label}
                      </td>
                      {quarterlyRatios.map((q) => {
                        const val = q[row.key] as number | null;
                        const isGrowth = row.key.includes('Buyume') || row.key === 'roe' || row.key === 'roa';
                        return (
                          <td
                            key={q.period as string}
                            className={`whitespace-nowrap px-3 py-2 text-right font-mono text-xs ${
                              isGrowth ? getGrowthColor(val) : 'text-gray-900 dark:text-gray-100'
                            }`}
                          >
                            {formatValue(val, row.format || 'number')}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
