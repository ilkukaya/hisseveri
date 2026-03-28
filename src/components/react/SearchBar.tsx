import { useState, useEffect, useRef, useMemo } from 'react';
import Fuse from 'fuse.js';

interface StockItem {
  ticker: string;
  name: string;
  sector: string;
}

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<StockItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [stocks, setStocks] = useState<StockItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/data/stocks.json')
      .then((r) => r.json())
      .then((data) => setStocks(data.stocks || []))
      .catch(() => {});
  }, []);

  const fuse = useMemo(
    () =>
      new Fuse(stocks, {
        keys: ['ticker', 'name'],
        threshold: 0.3,
        includeScore: true,
      }),
    [stocks],
  );

  useEffect(() => {
    if (query.length < 1) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    const matches = fuse.search(query).slice(0, 8).map((r) => r.item);
    setResults(matches);
    setIsOpen(matches.length > 0);
    setSelectedIndex(-1);
  }, [query, fuse]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navigate = (ticker: string) => {
    window.location.href = `/hisse/${ticker}`;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      navigate(results[selectedIndex].ticker);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length > 0 && results.length > 0 && setIsOpen(true)}
          placeholder="Hisse ara... (örn. FROTO)"
          className="w-full rounded-lg border-0 bg-navy-800 py-2 pl-9 pr-3 text-sm text-white placeholder-gray-400 outline-none ring-1 ring-navy-700 focus:ring-2 focus:ring-accent sm:w-64"
        />
      </div>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-1 w-full min-w-[280px] overflow-hidden rounded-lg border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900">
          {results.map((stock, i) => (
            <button
              key={stock.ticker}
              onClick={() => navigate(stock.ticker)}
              className={`flex w-full items-center gap-3 px-4 py-2.5 text-left transition ${
                i === selectedIndex ? 'bg-accent/10 dark:bg-accent/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              <span className="inline-flex items-center rounded bg-navy-900 px-2 py-0.5 font-mono text-xs font-bold text-white dark:bg-navy-700">
                {stock.ticker}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-gray-900 dark:text-white">{stock.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{stock.sector}</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
