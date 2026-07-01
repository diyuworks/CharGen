import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Send, Loader2 } from 'lucide-react';
import { api, normalizeAvatarUrl } from '../services/api';
import type { Character, ChatMessage } from '../types/character';

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [character, setCharacter] = useState<Character | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([api.getCharacter(id), api.getChatHistory(id)])
      .then(([char, history]) => {
        setCharacter(char);
        setMessages(history.messages);
      })
      .catch(() => setError('Could not load this character.'))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const handleSend = async () => {
    if (!input.trim() || !id || sending) return;
    const text = input.trim();
    setInput('');
    setError(null);

    const optimisticUser: ChatMessage = {
      id: `temp-${Date.now()}`,
      character_id: id,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, optimisticUser]);
    setSending(true);

    try {
      const reply = await api.sendChatMessage(id, text);
      setMessages(prev => [...prev, reply]);
    } catch (err: any) {
      setError(err.message || 'Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-zinc-950">
        <Loader2 size={24} className="text-white/30 animate-spin" />
      </div>
    );
  }

  if (!character) {
    return (
      <div className="h-screen flex flex-col items-center justify-center text-white/40 gap-3 bg-zinc-950">
        <p>Character not found.</p>
        <button onClick={() => navigate(-1)} className="text-violet-400 text-sm hover:text-violet-300">
          â† Go back
        </button>
      </div>
    );
  }

  const avatarSrc = normalizeAvatarUrl(character.avatar_url);

  return (
    <div
      className="h-screen max-h-screen flex flex-col overflow-hidden"
      style={{
        background:
          'radial-gradient(circle at 15% 10%, rgba(139,92,246,0.35), transparent 55%), radial-gradient(circle at 85% 90%, rgba(192,38,211,0.30), transparent 55%), radial-gradient(circle at 50% 50%, rgba(124,58,237,0.15), transparent 70%), #0a0a0f',
      }}
    >
      {/* Header */}
      <div className="sticky top-0 z-10 bg-zinc-950/80 backdrop-blur-md border-b border-white/8 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-xl hover:bg-white/8 text-white/50 hover:text-white transition-all shrink-0"
        >
          <ArrowLeft size={18} />
        </button>
        <div className="w-10 h-10 rounded-full overflow-hidden bg-violet-900/50 shrink-0 flex items-center justify-center ring-2 ring-violet-500/20">
          {avatarSrc ? (
            <img src={avatarSrc} alt={character.name} className="w-full h-full object-cover" />
          ) : (
            <span className="text-white/60 text-sm font-bold">
              {character.name.slice(0, 2).toUpperCase()}
            </span>
          )}
        </div>
        <div className="min-w-0">
          <h1 className="text-white font-semibold text-sm truncate">{character.name}</h1>
          <p className="text-white/40 text-xs truncate">{character.occupation}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-6 max-w-2xl w-full mx-auto">
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => {
            const prevMsg = messages[i - 1];
            const isSameSenderAsPrev = prevMsg && prevMsg.role === msg.role;
            const isAssistant = msg.role === 'assistant';

            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex items-end gap-2 ${isSameSenderAsPrev ? 'mt-1.5' : 'mt-5'} ${
                  isAssistant ? 'justify-start' : 'justify-end'
                }`}
              >
                {isAssistant && (
                  <div className="w-7 h-7 rounded-full overflow-hidden shrink-0 flex items-center justify-center bg-violet-900/50">
                    {!isSameSenderAsPrev && (
                      avatarSrc ? (
                        <img src={avatarSrc} alt={character.name} className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-white/60 text-[10px] font-bold">
                          {character.name.slice(0, 2).toUpperCase()}
                        </span>
                      )
                    )}
                  </div>
                )}

                <div className="flex flex-col max-w-[78%]">
                  <div
                    className={`rounded-2xl px-4 py-2.5 ${
                      isAssistant
                        ? `bg-white/8 border border-white/10 text-white/85 ${isSameSenderAsPrev ? 'rounded-tl-2xl' : 'rounded-tl-sm'}`
                        : `bg-gradient-to-br from-violet-600 to-purple-600 text-white shadow-lg shadow-violet-950/30 ${isSameSenderAsPrev ? 'rounded-tr-2xl' : 'rounded-tr-sm'}`
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  <span className={`text-[10px] text-white/25 mt-1 px-1 ${isAssistant ? 'text-left' : 'text-right'}`}>
                    {formatTime(msg.created_at)}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {sending && (
          <div className="flex items-end gap-2 mt-5 justify-start">
            <div className="w-7 h-7 rounded-full overflow-hidden shrink-0 flex items-center justify-center bg-violet-900/50">
              {avatarSrc ? (
                <img src={avatarSrc} alt={character.name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-white/60 text-[10px] font-bold">
                  {character.name.slice(0, 2).toUpperCase()}
                </span>
              )}
            </div>
            <div className="bg-white/8 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce" />
            </div>
          </div>
        )}

        {error && (
          <div className="text-center text-red-400 text-xs py-2">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/8 bg-zinc-950/80 backdrop-blur-md px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-end gap-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Message ${character.name}...`}
            rows={1}
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-white/30 resize-none focus:outline-none focus:border-violet-500/50 transition-colors max-h-32"
          />
          <motion.button
            whileTap={{ scale: 0.92 }}
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="p-2.5 bg-gradient-to-br from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-colors shrink-0 shadow-lg shadow-violet-950/30"
          >
            <Send size={16} />
          </motion.button>
        </div>
      </div>
    </div>
  );
}

