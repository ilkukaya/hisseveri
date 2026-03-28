export function getChangeColor(value: number | null | undefined): string {
  if (value == null) return 'text-gray-500';
  if (value > 0) return 'text-positive';
  if (value < 0) return 'text-negative';
  return 'text-gray-500';
}

export function getChangeColorClasses(value: number | null | undefined): string {
  if (value == null) return 'text-gray-500 dark:text-gray-400';
  if (value > 0) return 'text-emerald-600 dark:text-emerald-400';
  if (value < 0) return 'text-red-600 dark:text-red-400';
  return 'text-gray-500 dark:text-gray-400';
}

export function getChangeBg(value: number | null | undefined): string {
  if (value == null) return 'bg-gray-100 dark:bg-gray-800';
  if (value > 0) return 'bg-emerald-50 dark:bg-emerald-900/30';
  if (value < 0) return 'bg-red-50 dark:bg-red-900/30';
  return 'bg-gray-100 dark:bg-gray-800';
}

export function getChangeArrow(value: number | null | undefined): string {
  if (value == null) return '';
  if (value > 0) return '▲';
  if (value < 0) return '▼';
  return '';
}
