import { CATEGORIES } from '../types/character';

interface Props {
  selected: string;
  onChange: (category: string) => void;
}

export default function CategoryFilter({ selected, onChange }: Props) {
  return (
    <div className="flex gap-2 flex-wrap">
      <button
        onClick={() => onChange('')}
        className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
          !selected
            ? 'bg-violet-600 border-violet-500 text-white'
            : 'bg-white/5 border-white/10 text-white/50 hover:border-white/25 hover:text-white/80'
        }`}
      >
        All
      </button>
      {CATEGORIES.map(cat => (
        <button
          key={cat}
          onClick={() => onChange(cat === selected ? '' : cat)}
          className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
            selected === cat
              ? 'bg-violet-600 border-violet-500 text-white'
              : 'bg-white/5 border-white/10 text-white/50 hover:border-white/25 hover:text-white/80'
          }`}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
