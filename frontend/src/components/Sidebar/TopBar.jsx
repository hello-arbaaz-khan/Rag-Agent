import { useEffect, useRef, useState } from "react";
import { ChevronDown, LogOut, Moon, PanelRightClose, PanelRightOpen, Settings, Sun } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";

const TopBar = ({ onNavigate = () => {}, quickInfoOpen = false, onToggleQuickInfo = () => {} }) => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const initial = (user?.display_name || user?.username || user?.email || "A").charAt(0).toUpperCase();

  return (
    <header className="flex h-16 shrink-0 items-center justify-end gap-2 border-b border-slate-200 bg-white px-5 dark:border-white/5 dark:bg-[#0a0e17]">
      <button
        type="button"
        onClick={onToggleQuickInfo}
        title={quickInfoOpen ? "Hide quick info" : "Show quick info"}
        className="hidden h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5 lg:flex"
      >
        {quickInfoOpen ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
      </button>

      <button
        type="button"
        onClick={toggleTheme}
        title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"
      >
        {isDark ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
      </button>

      <div className="relative" ref={menuRef}>
        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          className="flex items-center gap-1.5 rounded-lg py-1 pl-1 pr-2 transition hover:bg-slate-100 dark:hover:bg-white/5"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 text-sm font-bold text-white">
            {initial}
          </div>
          <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition ${menuOpen ? "rotate-180" : ""}`} />
        </button>

        {menuOpen ? (
          <div className="absolute right-0 top-11 z-20 w-52 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg dark:border-white/10 dark:bg-[#12172a]">
            <div className="border-b border-slate-100 px-3.5 py-3 dark:border-white/5">
              <p className="truncate text-sm font-semibold text-slate-800 dark:text-white">
                {user?.display_name || user?.username || "Account"}
              </p>
              {user?.email ? <p className="truncate text-xs text-slate-400 dark:text-slate-500">{user.email}</p> : null}
            </div>
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                onNavigate("settings");
              }}
              className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm text-slate-600 transition hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-white/5"
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>
            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm text-red-500 transition hover:bg-red-50 dark:text-red-300 dark:hover:bg-red-500/10"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
};

export default TopBar;