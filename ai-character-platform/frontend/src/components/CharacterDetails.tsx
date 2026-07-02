import { motion, AnimatePresence } from 'framer-motion';
import { X, MapPin, Briefcase, Heart, BookOpen, Gamepad2, Brain, MessageCircle, RefreshCw, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import type { Character } from '../types/character';
import { api, normalizeAvatarUrl } from '../services/api';

interface Props {
  character: Character | null;
  onClose: () => void;
  onDelete?: (id: string) => void;
}

function Section({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="text-white/40 text-xs font-medium uppercase tracking-wider mb-2 flex items-center gap-1.5">
        <Icon size={12} />
        {title}
      </h4>
      {children}
    </div>
  );
}

export default function CharacterDetails({ character, onClose, onDelete }: Props) {
  const navigate = useNavigate();
  const [regenerating, setRegenerating] = useState(false);

  const handleRegenAvatar = async () => {
    if (!character) return;
    setRegenerating(true);
    const toastId = toast.loading("Regenerating avatar…");
    try {
      await api.generateAvatar(character.id);
      toast.success("Avatar regeneration started — refresh in a few seconds", { id: toastId, duration: 4000 });
    } catch {
      toast.error("Failed to start regeneration", { id: toastId });
    } finally {
      setRegenerating(false);
    }
  };

  const handleDelete = () => {
    if (!character || !onDelete) return;
    toast(t => (
      <div className="flex items-center gap-3">
        <span className="text-sm">Delete <b>{character.name}</b>?</span>
        <button
          onClick={() => { toast.dismiss(t.id); onDelete(character.id); onClose(); }}
          className="px-3 py-1 bg-red-500/80 hover:bg-red-500 text-white text-xs rounded-lg transition-colors"
        >
          Delete
        </button>
        <button
          onClick={() => toast.dismiss(t.id)}
          className="px-3 py-1 bg-white/10 hover:bg-white/20 text-white text-xs rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>
    ), { duration: 6000 });
  };

  return (
    <AnimatePresence>
      {character && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-zinc-950 border-l border-white/10 z-50 overflow-y-auto"
          >
            {/* Header */}
            <div className="sticky top-0 bg-zinc-950/95 backdrop-blur-sm border-b border-white/8 p-5 flex items-center justify-between">
              <div>
                <h2 className="text-white font-semibold text-lg">{character.name}</h2>
                <p className="text-white/40 text-sm">{character.occupation}</p>
              </div>
              <div className="flex items-center gap-2">
                {onDelete && (
                  <button
                    onClick={handleDelete}
                    className="p-2 rounded-xl hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-all"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
                <button onClick={onClose} className="p-2 rounded-xl hover:bg-white/8 text-white/50 hover:text-white transition-all">
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Avatar area */}
            <div className="relative aspect-square w-full bg-gradient-to-br from-violet-900/50 to-purple-900/50 flex items-center justify-center border-b border-white/8">
              {character.avatar_url ? (
                <img
                  src={normalizeAvatarUrl(character.avatar_url) ?? character.avatar_url}
                  alt={character.name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="text-center">
                  <div className="w-20 h-20 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-3xl font-bold text-white mx-auto mb-2">
                    {character.name.slice(0, 2).toUpperCase()}
                  </div>
                  <span className="text-white/30 text-xs">No avatar yet</span>
                </div>
              )}

              {/* Action buttons over avatar */}
              <div className="absolute bottom-3 left-3 right-3 flex gap-2 justify-between">
                <button
                  onClick={handleRegenAvatar}
                  disabled={regenerating}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-black/60 backdrop-blur-md hover:bg-black/80 text-white/70 hover:text-white text-xs font-medium rounded-full border border-white/10 transition-all disabled:opacity-50"
                >
                  <RefreshCw size={12} className={regenerating ? "animate-spin" : ""} />
                  {regenerating ? "Starting…" : "New Avatar"}
                </button>
                <motion.button
                  whileTap={{ scale: 0.96 }}
                  onClick={() => navigate(`/chat/${character.id}`)}
                  className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold rounded-full shadow-lg shadow-violet-900/40 transition-colors"
                >
                  <MessageCircle size={15} />
                  Chat
                </motion.button>
              </div>
            </div>

            {/* Content */}
            <div className="p-5 space-y-6">
              {/* Basic info */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white/5 rounded-xl p-3">
                  <div className="text-white/40 text-xs mb-1 flex items-center gap-1"><MapPin size={11} /> Nationality</div>
                  <div className="text-white text-sm font-medium">{character.nationality}</div>
                </div>
                <div className="bg-white/5 rounded-xl p-3">
                  <div className="text-white/40 text-xs mb-1">Age</div>
                  <div className="text-white text-sm font-medium">{character.age} years</div>
                </div>
                <div className="bg-white/5 rounded-xl p-3">
                  <div className="text-white/40 text-xs mb-1">Gender</div>
                  <div className="text-white text-sm font-medium capitalize">{character.gender || 'female'}</div>
                </div>
                <div className="bg-white/5 rounded-xl p-3 col-span-3">
                  <div className="text-white/40 text-xs mb-1 flex items-center gap-1"><Briefcase size={11} /> Category</div>
                  <div className="text-white text-sm font-medium">{character.category}</div>
                </div>
              </div>

              <Section title="Description" icon={BookOpen}>
                <p className="text-white/70 text-sm leading-relaxed">{character.description}</p>
              </Section>

              <Section title="Backstory" icon={Heart}>
                <p className="text-white/70 text-sm leading-relaxed">{character.backstory}</p>
              </Section>

              <Section title="Personality" icon={Brain}>
                <div className="flex flex-wrap gap-1.5">
                  {character.personality.map(t => (
                    <span key={t} className="text-xs bg-violet-500/15 border border-violet-500/30 text-violet-300 px-2.5 py-1 rounded-full">{t}</span>
                  ))}
                </div>
              </Section>

              <Section title="Emotional Traits" icon={Heart}>
                <div className="flex flex-wrap gap-1.5">
                  {character.emotional_traits.map(t => (
                    <span key={t} className="text-xs bg-rose-500/15 border border-rose-500/30 text-rose-300 px-2.5 py-1 rounded-full">{t}</span>
                  ))}
                </div>
              </Section>

              <Section title="Hobbies & Interests" icon={Gamepad2}>
                <div className="flex flex-wrap gap-1.5">
                  {[...character.hobbies, ...character.interests].map(item => (
                    <span key={item} className="text-xs bg-white/8 border border-white/10 text-white/60 px-2.5 py-1 rounded-full">{item}</span>
                  ))}
                </div>
              </Section>

              <Section title="Greeting" icon={Heart}>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-white/80 text-sm italic leading-relaxed">"{character.greeting}"</p>
                </div>
              </Section>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
