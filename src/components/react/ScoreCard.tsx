interface Karne {
  karlilik: number;
  buyume: number;
  borcluluk: number;
  toplam: number;
}

interface Props {
  karne: Karne | null;
}

function getScoreColor(score: number, max: number): string {
  const ratio = score / max;
  if (ratio >= 0.8) return 'text-green-500';
  if (ratio >= 0.5) return 'text-yellow-500';
  return 'text-red-500';
}

function getScoreBg(score: number, max: number): string {
  const ratio = score / max;
  if (ratio >= 0.8) return 'bg-green-500';
  if (ratio >= 0.5) return 'bg-yellow-500';
  return 'bg-red-500';
}

function ScoreBar({ score, max }: { score: number; max: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: max }, (_, i) => (
        <div
          key={i}
          className={`h-2 flex-1 rounded-sm ${
            i < score ? getScoreBg(score, max) : 'bg-gray-200 dark:bg-gray-700'
          }`}
        />
      ))}
    </div>
  );
}

export default function ScoreCard({ karne }: Props) {
  if (!karne) {
    return (
      <div className="flex h-[120px] items-center justify-center rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
        <p className="text-sm text-gray-400">Karne verisi mevcut değil</p>
      </div>
    );
  }

  const categories = [
    { label: 'Karlılık', score: karne.karlilik, max: 6 },
    { label: 'Büyüme', score: karne.buyume, max: 6 },
    { label: 'Borçluluk', score: karne.borcluluk, max: 6 },
  ];

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Finansal Karne</h3>
        <div className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${getScoreColor(karne.toplam, 18)}`}>
            {karne.toplam}
          </span>
          <span className="text-sm text-gray-400">/18</span>
        </div>
      </div>
      <div className="space-y-3">
        {categories.map((cat) => (
          <div key={cat.label}>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs text-gray-500 dark:text-gray-400">{cat.label}</span>
              <span className={`text-xs font-bold ${getScoreColor(cat.score, cat.max)}`}>
                {cat.score}/{cat.max}
              </span>
            </div>
            <ScoreBar score={cat.score} max={cat.max} />
          </div>
        ))}
      </div>
    </div>
  );
}
