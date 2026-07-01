import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Sparkles, Images, MessageCircle } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import GenerateCharacter from './pages/GenerateCharacter';
import Gallery from './pages/Gallery';
import ChatPage from './pages/ChatPage';
import ChatList from './pages/ChatList';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
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
    <div className="min-h-screen bg-zinc-950 text-white flex">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-white/8 flex flex-col p-4 sticky top-0 h-screen">
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
          <div className="px-2 text-white/20 text-xs">v1.0.0 · Gemini AI</div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/generate" element={<GenerateCharacter />} />
            <Route path="/gallery" element={<Gallery />} />
            <Route path="/chats" element={<ChatList />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
