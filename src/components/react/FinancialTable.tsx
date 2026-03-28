interface Props {
  periods: string[];
  rows: { label: string; values: number[] }[];
  title: string;
}

function formatValue(n: number): string {
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} Mlr`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} Mln`;
  return n.toLocaleString('tr-TR');
}

export default function FinancialTable({ periods, rows, title }: Props) {
  return (
    <div>
      <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full min-w-[600px] text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800">
              <th className="sticky left-0 z-10 bg-gray-50 px-4 py-2.5 text-left font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                Kalem
              </th>
              {periods.map((p) => (
                <th key={p} className="px-4 py-2.5 text-right font-semibold text-gray-700 dark:text-gray-300">
                  {p}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.label}
                className={`border-t border-gray-100 dark:border-gray-800 ${
                  i % 2 === 0 ? 'bg-white dark:bg-gray-900' : 'bg-gray-50/50 dark:bg-gray-900/50'
                }`}
              >
                <td className="sticky left-0 z-10 bg-inherit px-4 py-2 font-medium text-gray-800 dark:text-gray-200">
                  {row.label}
                </td>
                {row.values.map((val, j) => (
                  <td
                    key={j}
                    className={`px-4 py-2 text-right font-mono text-sm ${
                      val < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {formatValue(val)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
