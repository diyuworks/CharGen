import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, ImagePlus, Loader2 } from 'lucide-react';
import CharacterCard from '../components/CharacterCard';
import CharacterDetails from '../components/CharacterDetails';
import SearchBar from '../components/SearchBar';
import CategoryFilter from '../components/CategoryFilter';
import LoadingSpinner from '../components/LoadingSpinner';
import { api } from '../services/api';
import type { Character, CharacterListResponse } from '../types/character';

export default function Gallery() {
  const [data, setData] = useState<CharacterListResponse | null>(null);
  const [selected, setSelected] = useState<Character | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkMsg, setBulkMsg] = useState('');

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await api.getCharacters({
        page,
        page_size: 20,
        category: category || undefined,
        search: search || undefined,
      });
      setData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [page, category, search]);

  useEffect(() => {
    const t = setTimeout(load, search ? 400 : 0);
    return () => clearTimeout(t);
  }, [load, search]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this character?')) return;
    await api.deleteCharacter(id);
    load();
  };


  const handleBulkAvatars = async () => {
    setBulkLoading(true);
    setBulkMsg('');
    try {
      const result = await api.bulkGenerateAvatars(20);
      setBulkMsg(`✅ Generated avatars for ${result.updated} characters`);
      load();
    } catch (err) {
      setBulkMsg('❌ Failed to generate avatars');
    } finally {
      setBulkLoading(false);
      setTimeout(() => setBulkMsg(''), 4000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-white text-2xl font-bold">Character Gallery</h1>
          <p className="text-white/40 text-sm mt-1">
            {data ? `${data.total.toLocaleString()} characters` : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {bulkMsg && (
            <span className="text-sm text-white/60">{bulkMsg}</span>
          )}
          <button
            onClick={handleBulkAvatars}
            disabled={bulkLoading}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm rounded-xl transition-all"
          >
            {bulkLoading
              ? <><Loader2 size={14} className="animate-spin" /> Generating…</>
              : <><ImagePlus size={14} /> Generate All Avatars</>
            }
          </button>
        </div>
      </div>

      {/* Search + Filters */}
      <div className="space-y-3">
        <SearchBar value={search} onChange={v => { setSearch(v); setPage(1); }} />
        <CategoryFilter selected={category} onChange={v => { setCategory(v); setPage(1); }} />
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size={32} text="Loading characters…" />
        </div>
      ) : data?.characters.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-white/20 text-sm border border-dashed border-white/10 rounded-2xl">
          No characters found
        </div>
      ) : (
        <motion.div layout className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {data?.characters.map(char => (
            <CharacterCard
              key={char.id}
              character={char}
              onView={setSelected}
              onDelete={handleDelete}
            />
          ))}
        </motion.div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-4">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-2 rounded-xl bg-white/5 border border-white/10 text-white/50 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-white/50 text-sm">
            Page <span className="text-white">{page}</span> of <span className="text-white">{data.total_pages}</span>
          </span>
          <button
            onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
            disabled={page === data.total_pages}
            className="p-2 rounded-xl bg-white/5 border border-white/10 text-white/50 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      <CharacterDetails character={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
