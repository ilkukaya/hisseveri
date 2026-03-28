import { useState } from 'react';

interface Tab {
  label: string;
  content: React.ReactNode;
}

interface Props {
  tabs: Tab[];
  defaultIndex?: number;
}

export default function TabPanel({ tabs, defaultIndex = 0 }: Props) {
  const [activeIndex, setActiveIndex] = useState(defaultIndex);

  return (
    <div>
      <div className="flex gap-1 overflow-x-auto border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab, i) => (
          <button
            key={tab.label}
            onClick={() => setActiveIndex(i)}
            className={`whitespace-nowrap px-4 py-2.5 text-sm font-medium transition ${
              i === activeIndex
                ? 'border-b-2 border-accent text-accent'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="pt-4">{tabs[activeIndex]?.content}</div>
    </div>
  );
}
