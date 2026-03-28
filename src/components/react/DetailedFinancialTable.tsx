import type { DetailedFinancialItem } from '../../utils/types';

interface Props {
  periods: string[];
  items: DetailedFinancialItem[];
  title: string;
}

// Section header codes (level 0, bold, slightly different bg)
const SECTION_HEADERS = new Set(['1A', '1AK', '2A', '2B', '2N', '3B']);

// Total/subtotal codes (bold, top border)
const TOTAL_CODES = new Set(['1AI', '1BL', '2AAGG', '2ODB', '3D', '3DF', '3I', '3J', '3L']);

// Keywords that indicate a total/subtotal row
const TOTAL_KEYWORDS = ['TOPLAM', '(Ara Toplam)', 'BRÜT KAR', 'FAALİYET KARI', 'DÖNEM KARI', 'KAYNAKLAR'];

function isTotal(item: DetailedFinancialItem): boolean {
  if (TOTAL_CODES.has(item.code)) return true;
  const upper = item.name.toUpperCase();
  return TOTAL_KEYWORDS.some((kw) => upper.includes(kw.toUpperCase()));
}

function isSectionHeader(item: DetailedFinancialItem): boolean {
  return SECTION_HEADERS.has(item.code);
}

function getIndentLevel(code: string): number {
  // Section headers are always level 0
  if (SECTION_HEADERS.has(code)) return 0;

  // Determine level from code length relative to known patterns
  // Codes like 1AA, 1AB, 1AC, 2AA, 2BA, 3CA → level 1
  // Codes like 1AAG, 2AAG → level 2
  // Even deeper → level 3

  // For balance sheet (starts with 1 or 2)
  if (code.startsWith('1') || code.startsWith('2')) {
    // Remove leading digit(s) that represent section
    // 1A, 1AK, 2A, 2B, 2N are headers (level 0)
    // After header prefix, count additional chars for depth
    const prefixes = ['1AK', '1A', '2N', '2B', '2A'];
    for (const prefix of prefixes) {
      if (code.startsWith(prefix) && code !== prefix) {
        const suffix = code.slice(prefix.length);
        if (suffix.length <= 2) return 1;
        if (suffix.length <= 4) return 2;
        return 3;
      }
    }
    // Total codes at root level
    return 0;
  }

  // For income statement (starts with 3)
  if (code.startsWith('3')) {
    if (code.length <= 2) return 0;
    if (code.length <= 3) return 1;
    if (code.length <= 5) return 2;
    return 3;
  }

  // For cash flow (starts with 4)
  if (code.startsWith('4')) {
    const prefixes = ['4CBE', '4CAK', '4C', '4B'];
    for (const prefix of prefixes) {
      if (code.startsWith(prefix) && code !== prefix) {
        const suffix = code.slice(prefix.length);
        if (suffix.length <= 2) return 1;
        if (suffix.length <= 4) return 2;
        return 3;
      }
    }
    if (code.length <= 2) return 0;
    if (code.length <= 3) return 1;
    return 2;
  }

  return 0;
}

const INDENT_CLASSES = ['pl-4', 'pl-8', 'pl-12', 'pl-16'];

function formatValue(n: number): string {
  if (n === 0) return '-';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e9)
    return `${sign}${(abs / 1e9).toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} Mlr`;
  if (abs >= 1e6)
    return `${sign}${(abs / 1e6).toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} Mln`;
  if (abs >= 1e3)
    return `${sign}${(abs / 1e3).toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} Bin`;
  return n.toLocaleString('tr-TR');
}

export default function DetailedFinancialTable({ periods, items, title }: Props) {
  if (!items || items.length === 0) {
    return (
      <div className="flex h-[120px] items-center justify-center text-sm text-gray-400">
        Detayli veri mevcut degil
      </div>
    );
  }

  return (
    <div>
      <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full min-w-[600px] text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800">
              <th className="sticky left-0 z-10 min-w-[240px] bg-gray-50 px-4 py-2.5 text-left font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                Kalem
              </th>
              {periods.map((p) => (
                <th
                  key={p}
                  className="whitespace-nowrap px-4 py-2.5 text-right font-semibold text-gray-700 dark:text-gray-300"
                >
                  {p}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => {
              const level = getIndentLevel(item.code);
              const isTotalRow = isTotal(item);
              const isHeader = isSectionHeader(item);
              const isBold = isHeader || isTotalRow;

              const rowBg =
                isHeader
                  ? 'bg-gray-100 dark:bg-gray-800/80'
                  : i % 2 === 0
                    ? 'bg-white dark:bg-gray-900'
                    : 'bg-gray-50/50 dark:bg-gray-800/40';

              const topBorder = isTotalRow ? 'border-t-2 border-gray-300 dark:border-gray-600' : 'border-t border-gray-100 dark:border-gray-800';

              return (
                <tr key={item.code} className={topBorder}>
                  <td
                    className={`sticky left-0 z-10 whitespace-nowrap py-2 pr-4 ${INDENT_CLASSES[level]} ${rowBg} ${
                      isBold
                        ? 'font-semibold text-gray-900 dark:text-white'
                        : 'text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {item.name}
                  </td>
                  {item.values.map((val, j) => (
                    <td
                      key={j}
                      className={`whitespace-nowrap px-4 py-2 text-right font-mono text-sm ${rowBg} ${
                        isBold ? 'font-semibold' : ''
                      } ${val < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300'}`}
                    >
                      {formatValue(val)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
