import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Search, Sparkles, Users, Crown, Heart, Trash2 } from "lucide-react";
import { api, normalizeAvatarUrl } from "../services/api";
import type { Character } from "../types/character";
import { Link } from "react-router-dom";
import { useFavorites } from "../hooks/useFavorites";
import CharacterDetails from "../components/CharacterDetails";

const CATEGORIES = ["All", "❤️ Favorites", "College Student", "Researcher", "Fitness Trainer", "Artist", "Influencer", "Software Engineer"];

function CharacterCard({ character, onClick, onFavorite, isFav, onDelete }: {
  character: Character;
  onClick: () => void;
  onFavorite: (id: string) => void;
  isFav: boolean;
  onDelete: (id: string) => void;
}) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  const avatarSrc = normalizeAvatarUrl(character.avatar_url);
  const initials = character.name.split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase();
  const gradients = ["from-violet-600 to-purple-800","from-rose-500 to-pink-800","from-cyan-500 to-blue-800","from-emerald-500 to-teal-800","from-amber-500 to-orange-800","from-fuchsia-500 to-indigo-800"];
  const grad = gradients[character.name.charCodeAt(0) % gradients.length];
  const fakeCount = (character.name.charCodeAt(0) * 3917 + character.name.charCodeAt(1) * 1234) % 900000 + 100000;
  const isPopular = character.name.charCodeAt(0) % 3 === 0;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.2 }} onClick={onClick}
      className="relative rounded-2xl overflow-hidden cursor-pointer group border border-white/5 hover:border-white/20 transition-all"
      style={{ aspectRatio: "3/4" }}>
      {avatarSrc && !imgError ? (
        <>
          <img src={avatarSrc} alt={character.name}
            className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${imgLoaded ? "opacity-100" : "opacity-0"}`}
            onLoad={() => setImgLoaded(true)} onError={() => setImgError(true)} />
          {!imgLoaded && (
            <div className={`absolute inset-0 bg-gradient-to-br ${grad} flex items-center justify-center`}>
              <span className="text-white/30 text-4xl font-black">{initials}</span>
            </div>
          )}
        </>
      ) : (
        <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center`}>
          <span className="text-white/40 text-5xl font-black">{initials}</span>
        </div>
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />
      <div className="absolute top-3 left-3 right-3 flex justify-between items-start">
        <span className="text-xs bg-black/50 backdrop-blur-md text-white/70 px-2 py-0.5 rounded-full border border-white/10">{character.category}</span>
        {isPopular && (
          <span className="flex items-center gap-1 text-xs bg-amber-500/20 backdrop-blur-md text-amber-300 px-2 py-0.5 rounded-full border border-amber-500/20">
            <Crown size={10} /> Popular
          </span>
        )}
      </div>
      {/* Favorite + Delete buttons */}
      <div className="absolute top-3 right-3 z-30 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={e => { e.stopPropagation(); onFavorite(character.id); }}
          className="p-1.5 rounded-full bg-black/50 backdrop-blur-md border border-white/10 hover:border-white/25 transition-colors"
        >
          <Heart size={12} className={isFav ? "text-rose-400 fill-rose-400" : "text-white/50"} />
        </button>
        <button
          onClick={e => { e.stopPropagation(); onDelete(character.id); }}
          className="p-1.5 rounded-full bg-black/50 backdrop-blur-md border border-white/10 hover:border-red-500/40 transition-colors"
        >
          <Trash2 size={12} className="text-white/50" />
        </button>
      </div>
      <div className="absolute bottom-0 left-0 right-0 p-3">
        <h3 className="text-white font-bold text-sm leading-tight">{character.name}</h3>
        <p className="text-white/50 text-xs mt-0.5 line-clamp-2">{character.description?.slice(0, 80)}...</p>
        <div className="flex items-center gap-1 text-white/30 text-xs mt-2">
          <Users size={10} />
          <span>{fakeCount.toLocaleString()}</span>
          {isFav && <Heart size={10} className="text-rose-400 fill-rose-400 ml-1" />}
        </div>
      </div>
      <div className="absolute inset-0 bg-violet-600/10 opacity-0 group-hover:opacity-100 transition-opacity" />
    </motion.div>
  );
}

export default function Dashboard() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [selected, setSelected] = useState<Character | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [seed, setSeed] = useState(0);
  const { toggle, isFavorite } = useFavorites();

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this character?")) return;
    try {
      await api.deleteCharacter(id);
      setCharacters(c => c.filter(x => x.id !== id));
      setTotal(t => t - 1);
    } catch (err) {
      alert("Failed to delete");
    }
  };

  useEffect(() => {
    setLoading(true);
    api.getCharacters({
      page,
      page_size: 24,
      category: activeCategory !== "All" && activeCategory !== "❤️ Favorites" ? activeCategory : undefined,
      search: search || undefined,
    }).then(res => {
      setCharacters(res.characters.sort(() => Math.random() - 0.5));
      setTotal(res.total);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [page, activeCategory, search, seed]);

  const displayedCharacters = activeCategory === "❤️ Favorites"
    ? characters.filter(c => isFavorite(c.id))
    : characters;

  return (
    <div className="min-h-screen" style={{ background: "transparent" }}>
      <div className="sticky top-0 z-40 backdrop-blur-xl border-b border-white/5 px-6 py-4" style={{ background: "rgba(8,5,18,0.9)" }}>
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-violet-400" />
              <h1 className="text-white font-bold text-lg">Discover</h1>
              <span className="text-white/30 text-sm">{total.toLocaleString()} characters</span>
            </div>
            <button onClick={() => setSeed(s => s + 1)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-500/20 border border-violet-500/30 rounded-full text-violet-300 text-xs hover:bg-violet-500/30 transition-colors">
              <Sparkles size={12} /> Shuffle
            </button>
          </div>
          <div className="relative mb-3">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
            <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search characters..."
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-white text-sm placeholder-white/20 focus:outline-none focus:border-violet-500/40" />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {CATEGORIES.map(cat => (
              <button key={cat} onClick={() => { setActiveCategory(cat); setPage(1); }}
                className={`shrink-0 px-3 py-1 rounded-full text-xs font-medium transition-all ${activeCategory === cat ? "bg-violet-500 text-white" : "bg-white/5 text-white/40 hover:bg-white/10 hover:text-white/70"}`}>
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="max-w-6xl mx-auto px-6 py-6">
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="rounded-2xl bg-white/4 animate-pulse" style={{ aspectRatio: "3/4" }} />
            ))}
          </div>
        ) : displayedCharacters.length === 0 ? (
          <div className="text-center py-20 text-white/30">
            <Users size={32} className="mx-auto mb-3 opacity-30" />
            <p>{activeCategory === "❤️ Favorites" ? "No favorites yet — heart a character!" : "No characters found"}</p>
            {activeCategory !== "❤️ Favorites" && (
              <Link to="/generate" className="text-violet-400 text-sm mt-2 block hover:text-violet-300">Generate some →</Link>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {displayedCharacters.map(char => (
              <CharacterCard
                key={char.id}
                character={char}
                onClick={() => setSelected(char)}
                onFavorite={toggle}
                isFav={isFavorite(char.id)}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
        {total > 24 && activeCategory !== "❤️ Favorites" && (
          <div className="flex justify-center gap-2 mt-8">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white/50 text-sm disabled:opacity-30 hover:bg-white/10 transition-colors">Previous</button>
            <span className="px-4 py-2 text-white/30 text-sm">Page {page}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={characters.length < 24}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white/50 text-sm disabled:opacity-30 hover:bg-white/10 transition-colors">Next</button>
          </div>
        )}
      </div>
      {selected && (
        <CharacterDetails
          character={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}