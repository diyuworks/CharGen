import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ChevronDown } from 'lucide-react';
import { CATEGORIES, NATIONALITIES } from '../types/character';

interface Props {
  onGenerate: (category: string | undefined, nationality: string | undefined, count: number) => void;
  isLoading: boolean;
}

export default function CharacterGeneratorForm({ onGenerate, isLoading }: Props) {
  const [category, setCategory] = useState('');
  const [nationality, setNationality] = useState('');
  const [count, setCount] = useState(1);

  const handleSubmit = () => {
    onGenerate(
      category || undefined,
      nationality || undefined,
      count
    );
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
      <h2 className="text-white font-semibold text-lg mb-5 flex items-center gap-2">
        <Sparkles size={18} className="text-violet-400" />
        Generate Characters
      </h2>

      <div className="space-y-4">
        {/* Category */}
        <div>
          <label className="text-white/50 text-xs mb-1.5 block">Category <span className="text-white/30">(optional)</span></label>
          <div className="relative">
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white rounded-xl px-4 py-2.5 text-sm appearance-none focus:outline-none focus:border-violet-500/50 transition-colors"
            >
              <option value="">🎲 Random</option>
              {CATEGORIES.map(c => (
                <option key={c} value={c} className="bg-zinc-900">{c}</option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none" />
          </div>
        </div>

        {/* Nationality */}
        <div>
          <label className="text-white/50 text-xs mb-1.5 block">Nationality <span className="text-white/30">(optional)</span></label>
          <div className="relative">
            <select
              value={nationality}
              onChange={e => setNationality(e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white rounded-xl px-4 py-2.5 text-sm appearance-none focus:outline-none focus:border-violet-500/50 transition-colors"
            >
              <option value="">🌍 Random</option>
              {NATIONALITIES.map(n => (
                <option key={n} value={n} className="bg-zinc-900">{n}</option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none" />
          </div>
        </div>

        {/* Count */}
        <div>
          <label className="text-white/50 text-xs mb-1.5 block">
            Count: <span className="text-white">{count}</span>
          </label>
          <input
            type="range"
            min={1}
            max={20}
            value={count}
            onChange={e => setCount(Number(e.target.value))}
            className="w-full accent-violet-500"
          />
          <div className="flex justify-between text-white/30 text-xs mt-1">
            <span>1</span><span>10</span><span>20</span>
          </div>
        </div>

        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleSubmit}
          disabled={isLoading}
          className="w-full py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-all duration-200 flex items-center justify-center gap-2 mt-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Generate {count > 1 ? `${count} Characters` : 'Character'}
            </>
          )}
        </motion.button>
      </div>
    </div>
  );
}
