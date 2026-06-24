import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle } from 'lucide-react';
import CharacterGeneratorForm from '../components/CharacterGeneratorForm';
import CharacterCard from '../components/CharacterCard';
import CharacterDetails from '../components/CharacterDetails';
import { api } from '../services/api';
import type { Character } from '../types/character';

export default function GenerateCharacter() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selected, setSelected] = useState<Character | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // FIX: avatar generation runs as a backend BackgroundTask, so the initial
  // generate-character response always has avatar_url: "" — the real image
  // isn't ready yet. This polls each new character until its avatar shows up
  // (or we give up after maxAttempts) and patches it into state in place.
  const pollForAvatars = (ids: string[]) => {
    let attempt = 0;
    const maxAttempts = 20; // ~50s at 2.5s interval — covers Pollinations easily, most Stable Horde fallbacks too

    const interval = setInterval(async () => {
      attempt++;
      try {
        const updates = await Promise.all(
          ids.map(id => api.getCharacter(id).catch(() => null))
        );

        setCharacters(prev =>
          prev.map(c => {
            const fresh = updates.find(u => u && u.id === c.id);
            return fresh ?? c;
          })
        );

        const allDone = updates.every(u => u && u.avatar_url);
        if (allDone || attempt >= maxAttempts) {
          clearInterval(interval);
        }
      } catch {
        if (attempt >= maxAttempts) clearInterval(interval);
      }
    }, 2500);
  };

  const handleGenerate = async (
    category: string | undefined,
    nationality: string | undefined,
    gender: 'male' | 'female' | undefined,
    count: number
  ) => {
    setIsLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const result = await api.generateCharacters({ category, nationality, gender, count });
      setCharacters(result);
      setSuccessMsg(`✅ ${result.length} character${result.length > 1 ? 's' : ''} generated and saved!`);

      const pendingIds = result.filter(c => !c.avatar_url).map(c => c.id);
      if (pendingIds.length > 0) {
        pollForAvatars(pendingIds);
      }
    } catch (err: any) {
      setError(err.message || 'Generation failed. Check your Gemini API key.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-white text-2xl font-bold">Generate Characters</h1>
        <p className="text-white/40 text-sm mt-1">Create unique AI characters powered by Gemini</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <div>
          <CharacterGeneratorForm onGenerate={handleGenerate} isLoading={isLoading} />
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-4">
          {/* Notifications */}
          <AnimatePresence>
            {successMsg && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2 bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 rounded-xl px-4 py-3 text-sm"
              >
                <CheckCircle size={15} />
                {successMsg}
              </motion.div>
            )}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2 bg-red-500/15 border border-red-500/30 text-red-300 rounded-xl px-4 py-3 text-sm"
              >
                <AlertCircle size={15} />
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Loading placeholder */}
          {isLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-64 bg-white/5 border border-white/10 rounded-2xl animate-pulse" />
              ))}
            </div>
          )}

          {/* Generated characters */}
          {!isLoading && characters.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {characters.map(char => (
                <CharacterCard key={char.id} character={char} onView={setSelected} />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isLoading && characters.length === 0 && (
            <div className="h-64 flex items-center justify-center text-white/20 text-sm border border-dashed border-white/10 rounded-2xl">
              Generated characters will appear here
            </div>
          )}
        </div>
      </div>

      <CharacterDetails character={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
