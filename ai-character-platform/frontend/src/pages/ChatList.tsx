import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MessageCircle, Loader2 } from 'lucide-react';
import { api, normalizeAvatarUrl } from '../services/api';
import type { ChatListItem } from '../types/character';

function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

export default function ChatList() {
  const navigate = useNavigate();
  const [chats, setChats] = useState<ChatListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getChatList()
      .then(res => setChats(res.chats))
      .catch(() => setError('Could not load your chats.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 size={24} className="text-white/30 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-white text-2xl font-bold">Chats</h1>
        <p className="text-white/40 text-sm mt-1">Continue where you left off</p>
      </div>

      {error && (
        <div className="text-red-400 text-sm">{error}</div>
      )}

      {!error && chats.length === 0 && (
        <div className="h-64 flex flex-col items-center justify-center text-white/30 text-sm border border-dashed border-white/10 rounded-2xl gap-2">
          <MessageCircle size={28} className="opacity-30" />
          <p>No conversations yet</p>
          <p className="text-white/20 text-xs">Open a character's profile and hit Chat to start one</p>
        </div>
      )}

      {chats.length > 0 && (
        <div className="space-y-2">
          {chats.map((chat, i) => {
            const avatarSrc = normalizeAvatarUrl(chat.character_avatar_url);
            const isOwnMessage = chat.last_message_role === 'user';

            return (
              <motion.div
                key={chat.character_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => navigate(`/chat/${chat.character_id}`)}
                className="flex items-center gap-3 p-3 rounded-2xl bg-white/5 border border-white/8 hover:border-white/20 hover:bg-white/8 transition-all cursor-pointer"
              >
                <div className="w-12 h-12 rounded-full overflow-hidden bg-violet-900/50 shrink-0 flex items-center justify-center">
                  {avatarSrc ? (
                    <img src={avatarSrc} alt={chat.character_name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-white/60 text-sm font-bold">
                      {chat.character_name.slice(0, 2).toUpperCase()}
                    </span>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <h3 className="text-white font-medium text-sm truncate">{chat.character_name}</h3>
                    <span className="text-white/30 text-xs shrink-0">{formatRelativeTime(chat.last_message_at)}</span>
                  </div>
                  <p className="text-white/40 text-xs truncate mt-0.5">
                    {isOwnMessage && <span className="text-white/25">You: </span>}
                    {chat.last_message}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
