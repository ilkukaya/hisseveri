import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type SortingState,
  type ColumnDef,
} from '@tanstack/react-table';

interface Stock {
  ticker: string;
  name: string;
  sector: string;
  indexes: string[];
  price: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  pe: number | null;
  pb: number | null;
}

interface Props {
  stocks: Stock[];
  sectors: string[];
}

function fmt(n: number | null, decimals = 2): string {
  if (n == null) return '-';
  return n.toLocaleString('tr-TR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtLarge(n: number): string {
  if (n >= 1e9) return `${(n / 1e9).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} Mlr`;
  if (n >= 1e6) return `${(n / 1e6).toLocaleString('tr-TR', { maximumFractionDigits: 0 })} Mln`;
  return n.toLocaleString('tr-TR');
}

export default function StockListView({ stocks, sectors }: Props) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [sectorFilter, setSectorFilter] = useState('');
  const [indexFilter, setIndexFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredData = useMemo(() => {
    let result = stocks;
    if (sectorFilter) result = result.filter((s) => s.sector === sectorFilter);
    if (indexFilter) result = result.filter((s) => s.indexes.includes(indexFilter));
    if (searchQuery) {
      const q = searchQuery.toUpperCase();
      result = result.filter((s) => s.ticker.includes(q) || s.name.toUpperCase().includes(q));
    }
    return result;
  }, [stocks, sectorFilter, indexFilter, searchQuery]);

  const columns = useMemo<ColumnDef<Stock>[]>(
    () => [
      {
        accessorKey: 'ticker',
        header: 'Hisse',
        cell: ({ row }) => (
          <a href={`/hisse/${row.original.ticker}`} className="font-mono font-bold text-accent hover:underline">
            {row.original.ticker}
          </a>
        ),
      },
      {
        accessorKey: 'name',
        header: 'Şirket',
        cell: ({ getValue }) => <span className="max-w-[200px] truncate text-sm">{getValue() as string}</span>,
      },
      { accessorKey: 'sector', header: 'Sektör' },
      {
        accessorKey: 'price',
        header: 'Fiyat (₺)',
        cell: ({ getValue }) => <span className="font-mono">{fmt(getValue() as number)}</span>,
      },
      {
        accessorKey: 'changePercent',
        header: 'Değişim %',
        cell: ({ getValue }) => {
          const val = getValue() as number;
          const color = val > 0 ? 'text-emerald-600 dark:text-emerald-400' : val < 0 ? 'text-red-600 dark:text-red-400' : '';
          const arrow = val > 0 ? '▲' : val < 0 ? '▼' : '';
          return <span className={`font-mono font-medium ${color}`}>{arrow} {fmt(val)}%</span>;
        },
      },
      {
        accessorKey: 'marketCap',
        header: 'Piy. Değeri',
        cell: ({ getValue }) => <span className="font-mono text-sm">{fmtLarge(getValue() as number)}</span>,
      },
      {
        accessorKey: 'pe',
        header: 'F/K',
        cell: ({ getValue }) => <span className="font-mono">{fmt(getValue() as number | null)}</span>,
      },
      {
        accessorKey: 'pb',
        header: 'PD/DD',
        cell: ({ getValue }) => <span className="font-mono">{fmt(getValue() as number | null)}</span>,
      },
    ],
    [],
  );

  const table = useReactTable({
    data: filteredData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 50 } },
  });

  return (
    <div>
      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Hisse veya şirket ara..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent dark:border-gray-700 dark:bg-gray-900 dark:text-white"
        />
        <select
          value={sectorFilter}
          onChange={(e) => setSectorFilter(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-accent dark:border-gray-700 dark:bg-gray-900 dark:text-white"
        >
          <option value="">Tüm Sektörler</option>
          {sectors.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={indexFilter}
          onChange={(e) => setIndexFilter(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-accent dark:border-gray-700 dark:bg-gray-900 dark:text-white"
        >
          <option value="">Tüm Endeksler</option>
          <option value="BIST30">BIST30</option>
          <option value="BIST100">BIST100</option>
          <option value="BISTTUM">BIST TÜM</option>
        </select>
      </div>

      {/* Results count */}
      <p className="mb-3 text-sm text-gray-500 dark:text-gray-400">
        {filteredData.length} hisse listeleniyor
      </p>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full min-w-[800px] text-sm">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-gray-50 dark:bg-gray-800">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="cursor-pointer select-none px-4 py-2.5 text-left font-semibold text-gray-700 transition hover:text-accent dark:text-gray-300"
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {{ asc: ' ▲', desc: ' ▼' }[header.column.getIsSorted() as string] ?? ''}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, i) => (
              <tr
                key={row.id}
                className={`border-t border-gray-100 transition hover:bg-accent/5 dark:border-gray-800 ${
                  i % 2 === 0 ? 'bg-white dark:bg-gray-900' : 'bg-gray-50/50 dark:bg-gray-900/50'
                }`}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-2">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Sayfa {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-100 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Önceki
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-100 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Sonraki
          </button>
        </div>
      </div>
    </div>
  );
}
