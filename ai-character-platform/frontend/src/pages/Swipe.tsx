import { useEffect, useState, useRef, forwardRef, useImperativeHandle } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { Heart, X, Loader2, RotateCcw, MapPin, Briefcase } from 'lucide-react';
import { api, normalizeAvatarUrl } from '../services/api';
import { useFavorites } from '../hooks/useFavorites';
import type { Character } from '../types/character';

interface SwipeCardHandle {
  trigger: (direction: 1 | -1) => void;
}

interface SwipeCardProps {
  character: Character;
  isTop: boolean;
  depth: number;
  onRemove: (id: string, liked: boolean) => void;
}

const SwipeCard = forwardRef<SwipeCardHandle, SwipeCardProps>(
  ({ character, isTop, depth, onRemove }, ref) => {
    const x = useMotionValue(0);
    const rotate = useTransform(x, [-200, 200], [-18, 18]);
    const likeOpacity = useTransform(x, [20, 120], [0, 1]);
    const passOpacity = useTransform(x, [-120, -20], [1, 0]);
    const avatarSrc = normalizeAvatarUrl(character.avatar_url);

    const flyAway = (direction: 1 | -1) => {
      animate(x, direction * 500, {
        duration: 0.3,
        ease: 'easeOut',
        onComplete: () => onRemove(character.id, direction === 1),
      });
    };

    useImperativeHandle(ref, () => ({ trigger: flyAway }));

    return (
      <motion.div
        className="absolute inset-0"
        style={{
          x,
          rotate,
          scale: 1 - depth * 0.04,
          y: depth * 10,
          zIndex: 10 - depth,
        }}
        drag={isTop ? 'x' : false}
        onDragEnd={(_, info) => {
          if (info.offset.x > 120) flyAway(1);
          else if (info.offset.x < -120) flyAway(-1);
          else animate(x, 0, { type: 'spring', stiffness: 300, damping: 22 });
        }}
        initial={{ scale: 1 - depth * 0.04, opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="relative w-full h-full rounded-3xl overflow-hidden border border-white/10 shadow-2xl bg-zinc-900">
          {avatarSrc ? (
            <img
              src={avatarSrc}
              alt={character.name}
              className="w-full h-full object-cover"
              draggable={false}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-violet-900 to-zinc-900 text-white/40 text-6xl font-black">
              {character.name.slice(0, 1)}
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/10 to-transparent" />

          {isTop && (
            <>
              <motion.div
                style={{ opacity: likeOpacity }}
                className="absolute top-8 left-6 -rotate-12 border-4 border-emerald-400 text-emerald-400 font-black text-2xl px-3 py-1 rounded-xl pointer-events-none"
              >
                LIKE
              </motion.div>
              <motion.div
                style={{ opacity: passOpacity }}
                className="absolute top-8 right-6 rotate-12 border-4 border-rose-400 text-rose-400 font-black text-2xl px-3 py-1 rounded-xl pointer-events-none"
              >
                PASS
              </motion.div>
            </>
          )}

          <div className="absolute bottom-0 left-0 right-0 p-5">
            <h2 className="text-white font-bold text-2xl">
              {character.name}, {character.age}
            </h2>
            <div className="flex items-center gap-3 text-white/70 text-sm mt-1.5">
              <span className="flex items-center gap-1">
                <Briefcase size={13} />
                {character.occupation}
              </span>
              <span className="flex items-center gap-1">
                <MapPin size={13} />
                {character.nationality}
              </span>
            </div>
            <p className="text-white/50 text-xs mt-2 line-clamp-2">{character.description}</p>
          </div>
        </div>
      </motion.div>
    );
  }
);
SwipeCard.displayName = 'SwipeCard';

export default function Swipe() {
  const [stack, setStack] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const { toggle } = useFavorites();
  const topRef = useRef<SwipeCardHandle>(null);

  useEffect(() => {
    api
      .getCharacters({ page: 1, page_size: 50 })
      .then(res => {
        setStack(res.characters.sort(() => Math.random() - 0.5));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleRemove = (id: string, liked: boolean) => {
    if (liked) toggle(id);
    setStack(s => s.filter(c => c.id !== id));
  };

  const visible = stack.slice(0, 3);

  return (
    <div className="flex flex-col items-center" style={{ minHeight: 'calc(100vh - 8rem)' }}>
      <div className="relative w-full max-w-sm flex-1 my-4" style={{ minHeight: '480px' }}>
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-white/30">
            <Loader2 className="animate-spin" />
          </div>
        ) : visible.length === 0 ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white/30 text-center gap-2">
            <RotateCcw size={28} />
            <p>You've seen everyone for now</p>
          </div>
        ) : (
          visible
            .slice()
            .reverse()
            .map((char, i) => {
              const depth = visible.length - 1 - i;
              const isTop = depth === 0;
              return (
                <SwipeCard
                  key={char.id}
                  character={char}
                  isTop={isTop}
                  depth={depth}
                  onRemove={handleRemove}
                  ref={isTop ? topRef : undefined}
                />
              );
            })
        )}
      </div>

      {!loading && visible.length > 0 && (
        <div className="flex items-center gap-6 pb-6">
          <button
            onClick={() => topRef.current?.trigger(-1)}
            className="w-14 h-14 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-rose-400 hover:bg-rose-500/10 hover:border-rose-500/30 transition-colors"
          >
            <X size={22} />
          </button>
          <button
            onClick={() => topRef.current?.trigger(1)}
            className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/30 transition-colors"
          >
            <Heart size={24} />
          </button>
        </div>
      )}
    </div>
  );
}
