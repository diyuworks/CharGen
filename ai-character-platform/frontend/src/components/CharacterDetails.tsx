import { motion, AnimatePresence } from 'framer-motion';
import { X, Copy, Check, MapPin, Briefcase, Heart, BookOpen, Gamepad2, Brain } from 'lucide-react';
import { useState } from 'react';
import type { Character } from '../types/character';
import { normalizeAvatarUrl } from '../services/api';

interface Props {
  character: Character | null;
  onClose: () => void;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={copy} className="p-1.5 rounded-lg bg-white/8 hover:bg-white/15 text-white/50 hover:text-white transition-all">
      {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
    </button>
  );
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

export default function CharacterDetails({ character, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<'profile' | 'prompts'>('profile');

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
              <button onClick={onClose} className="p-2 rounded-xl hover:bg-white/8 text-white/50 hover:text-white transition-all">
                <X size={18} />
              </button>
            </div>

            {/* Avatar area */}
            <div className="h-48 bg-gradient-to-br from-violet-900/50 to-purple-900/50 flex items-center justify-center border-b border-white/8">
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
                  <span className="text-white/30 text-xs">Avatar will be generated</span>
                </div>
              )}
            </div>

            {/* Tabs */}
            <div className="flex border-b border-white/8">
              {(['profile', 'prompts'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-3 text-sm font-medium transition-colors capitalize ${
                    activeTab === tab ? 'text-white border-b-2 border-violet-500' : 'text-white/40 hover:text-white/70'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="p-5 space-y-6">
              {activeTab === 'profile' ? (
                <>
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
                </>
              ) : (
                <>
                  {/* System Prompt */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-white/40 text-xs font-medium uppercase tracking-wider">System Prompt</h4>
                      <CopyButton text={character.system_prompt} />
                    </div>
                    <div className="bg-zinc-900 border border-white/8 rounded-xl p-4">
                      <p className="text-white/70 text-xs leading-relaxed font-mono whitespace-pre-wrap">{character.system_prompt}</p>
                    </div>
                  </div>

                  {/* Avatar Prompt */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-white/40 text-xs font-medium uppercase tracking-wider">Avatar Prompt</h4>
                      <CopyButton text={character.avatar_prompt} />
                    </div>
                    <div className="bg-zinc-900 border border-white/8 rounded-xl p-4">
                      <p className="text-white/70 text-xs leading-relaxed font-mono">{character.avatar_prompt}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    <div className="bg-white/5 rounded-xl p-4">
                      <h4 className="text-white/40 text-xs mb-1">Communication Style</h4>
                      <p className="text-white/80 text-sm">{character.communication_style}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-4">
                      <h4 className="text-white/40 text-xs mb-1">Interaction Style</h4>
                      <p className="text-white/80 text-sm">{character.interaction_style}</p>
                    </div>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}