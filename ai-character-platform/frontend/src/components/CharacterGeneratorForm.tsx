import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ChevronDown } from 'lucide-react';
import { CATEGORIES, NATIONALITIES } from '../types/character';

interface Props {
  onGenerate: (category: string | undefined, nationality: string | undefined, gender: 'male' | 'female' | undefined, count: number) => void;
  isLoading: boolean;
}

// Plain Unicode symbols instead of lucide icons here — avoids depending on
// icons that may not exist in every installed lucide-react version.
const GENDER_OPTIONS = [
  { value: '' as const, label: 'Random', symbol: '🎲', ring: 'violet' as const },
  { value: 'female' as const, label: 'Female', symbol: '♀', ring: 'rose' as const },
  { value: 'male' as const, label: 'Male', symbol: '♂', ring: 'cyan' as const },
];

const ACTIVE_RING_STYLES: Record<string, string> = {
  violet: 'bg-violet-600/25 border-violet-500/60 text-white shadow-glow-violet',
  rose: 'bg-rose-600/20 border-rose-500/60 text-white shadow-glow-rose',
  cyan: 'bg-cyan-600/20 border-cyan-500/60 text-white shadow-glow-cyan',
};

export default function CharacterGeneratorForm({ onGenerate, isLoading }: Props) {
  const [category, setCategory] = useState('');
  const [nationality, setNationality] = useState('');
  const [gender, setGender] = useState<'male' | 'female' | ''>('');
  const [count, setCount] = useState(1);

  const handleSubmit = () => {
    onGenerate(
      category || undefined,
      nationality || undefined,
      gender || undefined,
      count
    );
  };

  return (
    <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm overflow-hidden">
      {/* Ambient corner glow — quiet signature touch, not on every element */}
      <div className="absolute -top-16 -right-16 w-40 h-40 bg-violet-600/20 rounded-full blur-3xl pointer-events-none" />

      <h2 className="relative text-white font-bold text-lg mb-5 flex items-center gap-2 tracking-tight">
        <Sparkles size={18} className="text-violet-400" />
        Generate Characters
      </h2>

      <div className="relative space-y-4">
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

        {/* Gender — icon-based instead of emoji, with a color identity per choice */}
        <div>
          <label className="text-white/50 text-xs mb-1.5 block">Gender</label>
          <div className="grid grid-cols-3 gap-2">
            {GENDER_OPTIONS.map(opt => {
              const active = gender === opt.value;
              return (
                <button
                  key={opt.value || 'random'}
                  type="button"
                  onClick={() => setGender(opt.value)}
                  className={`flex flex-col items-center gap-1 py-2.5 rounded-xl text-xs font-medium border transition-all duration-200 ${
                    active ? ACTIVE_RING_STYLES[opt.ring] : 'bg-white/5 border-white/10 text-white/50 hover:border-white/20 hover:text-white/70'
                  }`}
                >
                  <span className="text-base leading-none">{opt.symbol}</span>
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Count */}
        <div>
          <label className="text-white/50 text-xs mb-1.5 block">
            Count: <span className="text-white font-semibold">{count}</span>
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
          className="relative w-full py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:opacity-70 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 mt-2 overflow-hidden shadow-glow-violet"
        >
          {/* Signature shimmer sweep while generating — echoes the avatar "materializing" */}
          {isLoading && (
            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent w-1/2 animate-shimmer" />
          )}
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
