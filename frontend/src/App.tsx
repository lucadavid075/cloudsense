import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Resources from "./pages/Resources";
import { LayoutDashboard, MessageSquare, Search, Cloud } from "lucide-react";
import clsx from "clsx";

function Nav() {
  const links = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/chat", label: "AI Chat", icon: MessageSquare },
    { to: "/resources", label: "Idle Resources", icon: Search },
  ];

  return (
    <nav className="fixed left-0 top-0 h-full w-56 bg-[#0d1117] border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-5 border-b border-gray-800">
        <Cloud className="text-brand-500" size={22} />
        <span className="font-semibold text-white tracking-tight">CloudSense</span>
      </div>

      {/* Links */}
      <div className="flex flex-col gap-1 p-3 flex-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                  : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-800">
        <p className="text-xs text-gray-600 font-mono">AWS Cost Intelligence</p>
        <p className="text-xs text-gray-700 mt-0.5">v1.0.0</p>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        <Nav />
        <main className="ml-56 flex-1 p-8 min-h-screen">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/resources" element={<Resources />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
