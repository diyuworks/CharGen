import { useState, useEffect, useCallback } from "react";
import { api } from "../services/api";

export function useFavorites() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api.getFavorites()
      .then(res => setFavorites(res.character_ids))
      .catch(() => setFavorites([]))
      .finally(() => setLoaded(true));
  }, []);

  const toggle = useCallback((id: string) => {
    // Optimistic update — flip immediately, reconcile if the request fails
    setFavorites(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );

    api.toggleFavorite(id).catch(() => {
      // Revert on failure
      setFavorites(prev =>
        prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
      );
    });
  }, []);

  const isFavorite = useCallback((id: string) => favorites.includes(id), [favorites]);

  return { favorites, toggle, isFavorite, loaded };
}
