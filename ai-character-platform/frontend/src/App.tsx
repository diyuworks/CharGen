import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Sparkles, Images, MessageCircle, Heart } from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import Dashboard from './pages/Dashboard';
import GenerateCharacter from './pages/GenerateCharacter';
import Gallery from './pages/Gallery';
import ChatPage from './pages/ChatPage';
import ChatList from './pages/ChatList';
import Swipe from './pages/Swipe';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/swipe', icon: Heart, label: 'Swipe' },
  { to: '/generate', icon: Sparkles, label: 'Generate' },
  { to: '/gallery', icon: Images, label: 'Gallery' },
  { to: '/chats', icon: MessageCircle, label: 'Chats' },
];

function AppShell() {
  const location = useLocation();
  const isChatRoute = location.pathname.startsWith('/chat/');

  // Chat gets the full viewport — no sidebar, no content padding —
  // same pattern messaging apps use, so the conversation isn't squeezed.
  if (isChatRoute) {
    return (
      <Routes>
        <Route path="/chat/:id" element={<ChatPage />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col md:flex-row">
      {/* Sidebar — tablet/desktop only */}
      <aside className="hidden md:flex w-56 shrink-0 border-r border-white/8 flex-col p-4 sticky top-0 h-screen">
        {/* Logo */}
        <div className="px-2 mb-8 mt-2">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center shadow-glow-violet">
              <Sparkles size={14} className="text-white" />
            </div>
            <span className="font-bold text-white text-sm tracking-tight">FBN</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="space-y-1 flex-1">
          {NAV.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm transition-all duration-200 border-l-2 ${
                  isActive
                    ? 'bg-violet-600/20 border border-violet-500/30 border-l-violet-400 text-white'
                    : 'text-white/40 hover:text-white/80 hover:bg-white/5 border border-transparent border-l-transparent'
                }`
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/8 pt-4 mt-4">
          <div className="px-2 text-white/20 text-xs">v1.0.0 · Llama 3.1</div>
        </div>
      </aside>

      {/* Main — extra bottom padding on phone to clear the tab bar */}
      <main className="flex-1 p-4 md:p-8 overflow-auto pb-24 md:pb-8">
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/swipe" element={<Swipe />} />
            <Route path="/generate" element={<GenerateCharacter />} />
            <Route path="/gallery" element={<Gallery />} />
            <Route path="/chats" element={<ChatList />} />
          </Routes>
        </div>
      </main>

      {/* Bottom tab bar — phone only */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 z-50 bg-zinc-950/95 backdrop-blur-xl border-t border-white/8 flex items-stretch px-1 py-1.5"
        style={{ paddingBottom: 'calc(0.375rem + env(safe-area-inset-bottom))' }}
      >
        {NAV.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center gap-0.5 py-1.5 rounded-xl text-[10px] font-medium transition-colors ${
                isActive ? 'text-violet-300' : 'text-white/40'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="bottom-center"
        toastOptions={{
          style: {
            background: '#18181b',
            color: '#fff',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '12px',
            fontSize: '13px',
          },
          success: { iconTheme: { primary: '#a78bfa', secondary: '#18181b' } },
          error: { iconTheme: { primary: '#f43f5e', secondary: '#18181b' } },
        }}
      />
      <AppShell />
    </BrowserRouter>
  );
}
