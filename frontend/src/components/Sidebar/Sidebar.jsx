import { ChevronsLeft, ChevronsRight, Clock, FileText, LogOut, PenSquare, Search, Settings, Sparkles } from "lucide-react";
import { useAppContext } from "../../context/AppContext";
import { useAuth } from "../../context/AuthContext";

const NAV_ITEMS = [
  { id: "chat", label: "Chat History", icon: Clock },
  { id: "search", label: "Advanced Search", icon: Search },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings }
];

const timeAgo = (isoString) => {
  if (!isoString) return "";
  const diffMs = Date.now() - new Date(isoString).getTime();
  if (Number.isNaN(diffMs) || diffMs < 0) return "";
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

const SidebarSkeleton = () => (
  <div className="space-y-2">
    {[0, 1, 2].map((item) => (
      <div key={item} className="h-11 animate-pulse rounded-lg bg-slate-200 dark:bg-white/5" />
    ))}
  </div>
);

const Sidebar = ({
  onUploadClick,
  activeView = "chat",
  onNavigate = () => {},
  collapsed = false,
  onToggleCollapse = () => {}
}) => {
  const { documents, selectedDocumentId, loadingDocuments, apiError, dispatch } = useAppContext();
  const { user, logout } = useAuth();

  const handleSelectChat = (documentId) => {
    dispatch({ type: "SET_SELECTED_DOCUMENT", payload: documentId });
    onNavigate("chat");
  };

  const handleNewChat = () => {
    dispatch({ type: "SET_SELECTED_DOCUMENT", payload: null });
    onNavigate("chat");
  };

  if (collapsed) {
    return (
      <aside className="flex h-full w-[76px] flex-col items-center gap-4 border-r border-slate-200 bg-white py-4 dark:border-white/5 dark:bg-[#0b0f19]">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg shadow-blue-950/20">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <button
          type="button"
          onClick={onToggleCollapse}
          title="Expand sidebar"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"
        >
          <ChevronsRight className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={handleNewChat}
          title="New chat"
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md transition hover:bg-blue-500"
        >
          <PenSquare className="h-4 w-4" />
        </button>
        <nav className="mt-2 flex flex-col items-center gap-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                title={item.label}
                onClick={() => onNavigate(item.id)}
                className={`flex h-10 w-10 items-center justify-center rounded-lg transition ${
                  isActive
                    ? "bg-blue-50 text-blue-600 dark:bg-blue-500/15 dark:text-blue-300"
                    : "text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"
                }`}
              >
                <Icon className="h-4 w-4" />
              </button>
            );
          })}
        </nav>
        <div className="mt-auto flex flex-col items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 text-sm font-bold text-white">
            {(user?.display_name || user?.username || user?.email || "A").charAt(0).toUpperCase()}
          </div>
          <button
            type="button"
            onClick={logout}
            title="Log out"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-red-50 hover:text-red-500 dark:text-slate-400 dark:hover:bg-red-500/10 dark:hover:text-red-300"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-200 bg-white p-4 dark:border-white/5 dark:bg-[#0b0f19] lg:w-[300px]">
      <div className="mb-5 flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg shadow-blue-950/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-base font-bold text-slate-900 dark:text-white">RAG Agent</h1>
            <p className="truncate text-xs text-slate-500 dark:text-slate-400">Chat with your documents</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onToggleCollapse}
          title="Collapse sidebar"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"
        >
          <ChevronsLeft className="h-4 w-4" />
        </button>
      </div>

      <button
        type="button"
        onClick={handleNewChat}
        className={`flex w-full items-center gap-2 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition ${
          activeView === "chat" && !selectedDocumentId
            ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
            : "border border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:hover:bg-white/[0.06]"
        }`}
      >
        <PenSquare className="h-4 w-4" />
        New Chat
      </button>

      <nav className="mt-3 space-y-1">
        {NAV_ITEMS.filter((item) => item.id !== "chat").map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`flex w-full items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-300"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/5"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="mt-5 flex items-center justify-between px-0.5">
        <h2 className="text-xs font-bold uppercase tracking-wide text-slate-400 dark:text-slate-500">Recent Chats</h2>
        {documents.length ? (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-500 dark:bg-white/5 dark:text-slate-400">
            {documents.length}
          </span>
        ) : null}
      </div>

      <div className="mt-2 min-h-0 flex-1 overflow-y-auto pr-1">
        {loadingDocuments ? <SidebarSkeleton /> : null}

        {!loadingDocuments && apiError ? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-600 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
            {apiError}
          </div>
        ) : null}

        {!loadingDocuments && !apiError && documents.length === 0 ? (
          <button
            type="button"
            onClick={onUploadClick}
            className="w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center transition hover:border-blue-400 hover:bg-blue-50/40 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-blue-500/40 dark:hover:bg-blue-500/5"
          >
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">No chats yet</p>
            <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">Upload a document to start</p>
          </button>
        ) : null}

        <div className="space-y-1">
          {documents.map((document) => (
            <button
              key={document.id}
              type="button"
              onClick={() => handleSelectChat(document.id)}
              className={`group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left transition ${
                document.id === selectedDocumentId
                  ? "bg-blue-50 dark:bg-white/[0.06]"
                  : "hover:bg-slate-100 dark:hover:bg-white/[0.04]"
              }`}
            >
              <FileText className="h-4 w-4 shrink-0 text-slate-400 dark:text-slate-500" />
              <span className="min-w-0 flex-1 truncate text-sm text-slate-700 dark:text-slate-300">{document.name}</span>
              <span className="shrink-0 text-[11px] text-slate-400 dark:text-slate-500">
                {timeAgo(document.created_at || document.updated_at)}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-slate-200 pt-3 dark:border-white/5">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 text-sm font-bold text-white">
            {(user?.display_name || user?.username || user?.email || "A").charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-800 dark:text-white">
              {user?.display_name || user?.username || "Account"}
            </p>
            {user?.email ? <p className="truncate text-xs text-slate-400 dark:text-slate-500">{user.email}</p> : null}
          </div>
        </div>
        <button
          type="button"
          onClick={logout}
          title="Log out"
          aria-label="Log out"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-red-50 hover:text-red-500 dark:text-slate-500 dark:hover:bg-red-500/10 dark:hover:text-red-300"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;