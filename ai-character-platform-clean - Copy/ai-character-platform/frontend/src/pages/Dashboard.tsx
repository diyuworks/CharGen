import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Users, Sparkles, TrendingUp, Zap, ArrowRight, Star } from 'lucide-react';
import { api } from '../services/api';
import type { StatsResponse } from '../types/character';
import { Link } from 'react-router-dom';

const CATEGORY_EMOJIS: Record<string, string> = {
  'Doctor': '🩺', 'Software Engineer': '💻', 'Artist': '🎨',
  'Fitness Trainer': '💪', 'Teacher': '📚', 'Entrepreneur': '🚀',
  'Musician': '🎵', 'Photographer': '📷', 'Writer': '✍️',
  'Gamer': '🎮', 'Travel Blogger': '✈️', 'Fashion Designer': '👗',
  'Influencer': '⭐', 'Life Coach': '🧠', 'Researcher': '🔬',
  'College Student': '🎓',
};

function StatCard({ icon: Icon, label, value, gradient, delay }: {
  icon: any; label: string; value: string | number; gradient: string; delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
      className="relative overflow-hidden rounded-2xl p-6 border border-white/8"
      style={{ background: 'rgba(255,255,255,0.03)' }}
    >
      {/* Glow blob */}
      <div className={`absolute -top-6 -right-6 w-24 h-24 rounded-full blur-2xl opacity-20 ${gradient}`} />
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${gradient}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div className="text-3xl font-black text-white tracking-tight">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div className="text-white/40 text-xs mt-1 font-medium uppercase tracking-widest">{label}</div>
    </motion.div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats().then(s => { setStats(s); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const topCategories = stats
    ? Object.entries(stats.by_category).sort((a, b) => b[1] - a[1]).slice(0, 6)
    : [];

  const maxCount = topCategories[0]?.[1] ?? 1;

  return (
    <div className="space-y-8 pb-8">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-end justify-between"
      >
        <div>
          <p className="text-white/30 text-xs font-medium uppercase tracking-widest mb-1">Overview</p>
          <h1 className="text-white text-3xl font-black tracking-tight">Character Platform</h1>
        </div>
        <Link to="/generate">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold rounded-xl transition-colors"
          >
            <Sparkles size={14} />
            Generate
          </motion.button>
        </Link>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          icon={Users}
          label="Total Characters"
          value={loading ? '...' : (stats?.total_characters ?? 0)}
          gradient="bg-gradient-to-br from-violet-500 to-purple-600"
          delay={0}
        />
        <StatCard
          icon={Star}
          label="Categories"
          value={loading ? '...' : Object.keys(stats?.by_category ?? {}).length}
          gradient="bg-gradient-to-br from-rose-500 to-pink-600"
          delay={0.08}
        />
        <StatCard
          icon={TrendingUp}
          label="Avg per Category"
          value={loading ? '...' : (stats ? Math.round(stats.total_characters / Math.max(Object.keys(stats.by_category).length, 1)) : 0)}
          gradient="bg-gradient-to-br from-cyan-500 to-blue-600"
          delay={0.16}
        />
        <StatCard
          icon={Zap}
          label="Ready for Chat"
          value={loading ? '...' : (stats?.total_characters ?? 0)}
          gradient="bg-gradient-to-br from-emerald-500 to-teal-600"
          delay={0.24}
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* Category breakdown — wider */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-3 rounded-2xl border border-white/8 p-6"
          style={{ background: 'rgba(255,255,255,0.03)' }}
        >
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-white font-bold text-base">Characters by Category</h2>
            <span className="text-white/30 text-xs">{topCategories.length} active</span>
          </div>

          {topCategories.length === 0 ? (
            <div className="h-40 flex items-center justify-center text-white/20 text-sm">
              No characters yet — generate some!
            </div>
          ) : (
            <div className="space-y-3">
              {topCategories.map(([cat, count], i) => {
                const pct = (count / maxCount) * 100;
                return (
                  <motion.div
                    key={cat}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.35 + i * 0.05 }}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-base">{CATEGORY_EMOJIS[cat] ?? '👤'}</span>
                        <span className="text-white/70 text-sm">{cat}</span>
                      </div>
                      <span className="text-white/40 text-xs tabular-nums">{count}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.8, delay: 0.4 + i * 0.05, ease: [0.23, 1, 0.32, 1] }}
                        className="h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-400"
                      />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>

        {/* Quick Actions — narrower */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="lg:col-span-2 flex flex-col gap-3"
        >
          {/* Generate CTA */}
          <Link to="/generate" className="flex-1">
            <motion.div
              whileHover={{ y: -2, scale: 1.01 }}
              className="h-full min-h-32 relative overflow-hidden rounded-2xl p-5 cursor-pointer border border-violet-500/30 hover:border-violet-500/60 transition-all"
              style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.15), rgba(139,92,246,0.08))' }}
            >
              <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-violet-500/10 blur-2xl" />
              <Sparkles size={22} className="text-violet-400 mb-3" />
              <h3 className="text-white font-bold text-base">Generate</h3>
              <p className="text-white/40 text-xs mt-1 leading-relaxed">Create new AI female characters</p>
              <div className="flex items-center gap-1 mt-3 text-violet-400 text-xs font-semibold">
                Start now <ArrowRight size={12} />
              </div>
            </motion.div>
          </Link>

          {/* Gallery CTA */}
          <Link to="/gallery" className="flex-1">
            <motion.div
              whileHover={{ y: -2, scale: 1.01 }}
              className="h-full min-h-32 relative overflow-hidden rounded-2xl p-5 cursor-pointer border border-white/8 hover:border-white/20 transition-all"
              style={{ background: 'rgba(255,255,255,0.03)' }}
            >
              <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-white/5 blur-2xl" />
              <Users size={22} className="text-white/50 mb-3" />
              <h3 className="text-white font-bold text-base">Gallery</h3>
              <p className="text-white/40 text-xs mt-1 leading-relaxed">Browse all your characters</p>
              <div className="flex items-center gap-1 mt-3 text-white/30 text-xs font-semibold">
                View all <ArrowRight size={12} />
              </div>
            </motion.div>
          </Link>
        </motion.div>
      </div>

      {/* Footer note */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="text-white/15 text-xs text-center"
      >
        Powered by NVIDIA LLaMA · Avatars by Pollinations.ai
      </motion.p>
    </div>
  );
}
