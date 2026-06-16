import { motion } from 'framer-motion';
import { MapPin, Briefcase, Trash2, Eye, Loader2, Heart } from 'lucide-react';
import { useState, useEffect } from 'react';
import type { Character } from '../types/character';

interface Props {
  character: Character;
  onView: (character: Character) => void;
  onDelete?: (id: string) => void;
}

const ACCENT_COLORS = [
  'from-violet-500 to-purple-600',
  'from-rose-500 to-pink-600',
  'from-cyan-500 to-blue-600',
  'from-emerald-500 to-teal-600',
  'from-amber-500 to-orange-600',
  'from-fuchsia-500 to-indigo-600',
];

const SOLID_ACCENTS = [
  'bg-violet-500', 'bg-rose-500', 'bg-cyan-500',
  'bg-emerald-500', 'bg-amber-500', 'bg-fuchsia-500',
];

const BG_COLORS = [
  '#1e1030', '#2d1020', '#0a1a2d', '#0a2018', '#2d1a00', '#1a0a2d',
];

function getIdx(name: string) {
  return name.charCodeAt(0) % ACCENT_COLORS.length;
}

function getInitials(name: string) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
}

function buildLoreleiUrl(character: Character): string {
  const seed = encodeURIComponent(character.name + character.nationality);
  const colors = ['b6e3f4', 'c0aede', 'd1d4f9', 'ffd5dc', 'ffdfbf', 'c1f4c5'];
  const color = colors[character.name.charCodeAt(0) % colors.length];
  return `https://api.dicebear.com/7.x/lorelei/png?seed=${seed}&backgroundColor=${color}&size=256`;
}

export default function CharacterCard({ character, onView, onDelete }: Props) {
  const idx = getIdx(character.name);
  const accent = ACCENT_COLORS[idx];
  const solidAccent = SOLID_ACCENTS[idx];
  const bgColor = BG_COLORS[idx];

  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [liked, setLiked] = useState(false);

  // Determine avatar source
  const isRealPhoto = character.avatar_url?.includes('localhost:8000/static');
  const avatarSrc = isRealPhoto
    ? character.avatar_url
    : buildLoreleiUrl(character); // Always use lorelei as default

  useEffect(() => {
    setImgLoaded(false);
    setImgError(false);
  }, [character.id, character.avatar_url]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 24, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      className="group relative rounded-2xl overflow-hidden border border-white/8 hover:border-white/20 transition-colors duration-300 cursor-pointer"
      style={{ background: 'rgba(10,10,15,0.9)' }}
      onClick={() => onView(character)}
    >
      {/* Avatar section */}
      <div
        className="relative h-52 overflow-hidden flex items-center justify-center"
        style={{ backgroundColor: bgColor }}
      >
        {/* Gradient background */}
        <div className={`absolute inset-0 bg-gradient-to-br ${accent} opacity-20`} />

        {/* Avatar image */}
        {!imgError && (
          <img
            src={avatarSrc!}
            alt={character.name}
            className={`transition-all duration-700 z-10 relative ${
              isRealPhoto
                ? `w-full h-full object-cover absolute inset-0 ${imgLoaded ? 'opacity-100' : 'opacity-0'}`
                : `w-44 h-44 object-contain ${imgLoaded ? 'opacity-100' : 'opacity-0'}`
            }`}
            onLoad={() => setImgLoaded(true)}
            onError={() => setImgError(true)}
          />
        )}

        {/* Loading spinner */}
        {!imgLoaded && !imgError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 z-20">
            <Loader2 size={24} className="text-white/30 animate-spin" />
            <span className="text-white/20 text-xs">Loading…</span>
          </div>
        )}

        {/* Error fallback — initials */}
        {imgError && (
          <div className="flex flex-col items-center justify-center gap-2 z-10">
            <div className={`w-16 h-16 rounded-full ${solidAccent} opacity-40 flex items-center justify-center`}>
              <span className="text-white font-black text-xl">{getInitials(character.name)}</span>
            </div>
          </div>
        )}

        {/* Gradient overlay bottom */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none z-10" />

        {/* Category badge */}
        <div className="absolute top-3 left-3 right-3 flex items-start justify-between z-20">
          <span className="bg-black/50 backdrop-blur-md text-white/80 text-xs px-2.5 py-1 rounded-full border border-white/10 font-medium">
            {character.category}
          </span>
          <div className="flex gap-1.5">
            <motion.button
              whileTap={{ scale: 0.8 }}
              onClick={e => { e.stopPropagation(); setLiked(l => !l); }}
              className="p-1.5 bg-black/40 backdrop-blur-md rounded-full border border-white/10 hover:border-white/25 transition-colors"
            >
              <Heart size={12} className={liked ? 'text-rose-400 fill-rose-400' : 'text-white/50'} />
            </motion.button>
            {onDelete && (
              <motion.button
                whileTap={{ scale: 0.8 }}
                onClick={e => { e.stopPropagation(); onDelete(character.id); }}
                className="p-1.5 bg-black/40 backdrop-blur-md rounded-full border border-white/10 hover:border-red-500/40 transition-colors opacity-0 group-hover:opacity-100"
              >
                <Trash2 size={12} className="text-white/50" />
              </motion.button>
            )}
          </div>
        </div>

        {/* View on hover */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200 z-20">
          <button
            onClick={() => onView(character)}
            className="flex items-center gap-2 px-4 py-2 bg-white/15 backdrop-blur-md border border-white/25 rounded-full text-white text-xs font-semibold hover:bg-white/25 transition-colors"
          >
            <Eye size={12} /> View Profile
          </button>
        </div>
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-white font-bold text-base leading-tight truncate">{character.name}</h3>
          <span className="text-white/20 text-xs shrink-0 mt-0.5">{character.age}y</span>
        </div>
        <div className="mt-1.5 space-y-1">
          <div className="flex items-center gap-1.5 text-white/40 text-xs">
            <Briefcase size={10} className="shrink-0" />
            <span className="truncate">{character.occupation}</span>
          </div>
          <div className="flex items-center gap-1.5 text-white/40 text-xs">
            <MapPin size={10} className="shrink-0" />
            <span className="truncate">{character.nationality}</span>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-1">
          {character.personality.slice(0, 3).map((trait, i) => (
            <motion.span
              key={trait}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="text-xs text-white/50 px-2 py-0.5 rounded-full border border-white/8"
              style={{ background: 'rgba(255,255,255,0.04)' }}
            >
              {trait}
            </motion.span>
          ))}
        </div>
        <div className={`mt-4 h-0.5 rounded-full bg-gradient-to-r ${accent} opacity-30`} />
      </div>
    </motion.div>
  );
}
