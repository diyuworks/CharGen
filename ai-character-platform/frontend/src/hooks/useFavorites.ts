import { useState, useEffect } from "react";

export function useFavorites() {
  const [favorites, setFavorites] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("waifu_favorites") || "[]");
    } catch { return []; }
  });

  useEffect(() => {
    localStorage.setItem("waifu_favorites", JSON.stringify(favorites));
  }, [favorites]);

  const toggle = (id: string) => {
    setFavorites(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const isFavorite = (id: string) => favorites.includes(id);

  return { favorites, toggle, isFavorite };
}
