import type { Character, CharacterListResponse, GenerateRequest, StatsResponse } from '../types/character';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';
export const BACKEND_BASE = BASE_URL.replace(/\/api\/v1\/?$/i, '');

export function normalizeAvatarUrl(rawAvatar?: string | null): string | null {
  if (!rawAvatar) return null;

  const normalized = rawAvatar
    .replace(/^http:\/\/localhost:8000/, BACKEND_BASE)
    .replace(/^https?:\/\/127\.0\.0\.1:8000/, BACKEND_BASE);

  if (normalized.startsWith('http')) {
    return normalized;
  }

  if (normalized.includes('/static/')) {
    return `${BACKEND_BASE}${normalized.startsWith('/') ? '' : '/'}${normalized}`;
  }

  return null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  generateCharacters: (data: GenerateRequest): Promise<Character[]> =>
    request('/generate-character?save=true&auto_avatar=true', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getCharacters: (params: {
    page?: number;
    page_size?: number;
    category?: string;
    nationality?: string;
    search?: string;
  }): Promise<CharacterListResponse> => {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));
    if (params.category) query.set('category', params.category);
    if (params.nationality) query.set('nationality', params.nationality);
    if (params.search) query.set('search', params.search);
    return request(`/characters?${query.toString()}`);
  },

  getCharacter: (id: string): Promise<Character> =>
    request(`/character/${id}`),

  deleteCharacter: (id: string): Promise<void> =>
    request(`/character/${id}`, { method: 'DELETE' }),

  getStats: (): Promise<StatsResponse> =>
    request('/characters/stats'),

  generateAvatar: (id: string): Promise<{ avatar_url: string; character_id: string }> =>
    request(`/character/${id}/generate-avatar`, { method: 'POST' }),

  bulkGenerateAvatars: (limit: number = 20): Promise<{ updated: number; total_processed: number }> =>
    request(`/characters/generate-avatars-bulk?limit=${limit}`, { method: 'POST' }),
};
