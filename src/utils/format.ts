const trFormatter = new Intl.NumberFormat('tr-TR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const trIntFormatter = new Intl.NumberFormat('tr-TR', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function formatNumber(n: number | null | undefined, decimals = 2): string {
  if (n == null || isNaN(n)) return '-';
  if (decimals === 0) return trIntFormatter.format(n);
  return trFormatter.format(n);
}

export function formatCurrency(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '-';
  return `₺${trFormatter.format(n)}`;
}

export function formatPercent(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '-';
  const sign = n > 0 ? '+' : '';
  return `${sign}${trFormatter.format(n)}%`;
}

export function formatLargeNumber(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '-';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e12) return `${sign}${trFormatter.format(abs / 1e12)} Trilyon`;
  if (abs >= 1e9) return `${sign}${trFormatter.format(abs / 1e9)} Milyar`;
  if (abs >= 1e6) return `${sign}${trFormatter.format(abs / 1e6)} Milyon`;
  if (abs >= 1e3) return `${sign}${trIntFormatter.format(abs)}`;
  return `${sign}${trFormatter.format(abs)}`;
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('tr-TR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function formatShortDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('tr-TR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}
