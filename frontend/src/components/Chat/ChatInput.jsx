import { useEffect, useRef, useState } from "react";
import { ChevronDown, Globe, Paperclip, SendHorizontal, Sparkles } from "lucide-react";

const SEARCH_MODES = ["Search mode", "Fast", "Deep research"];

const ChatInput = ({ value, setValue, onSubmit, disabled, loading, onAttachClick, floating = false, inputRef }) => {
  const [mode, setMode] = useState(SEARCH_MODES[0]);
  const [modeOpen, setModeOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setModeOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
      className={floating ? "" : "border-t border-slate-200 bg-white/80 p-4 dark:border-slate-800 dark:bg-slate-950/80"}
    >
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm transition focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-500/15 dark:border-white/10 dark:bg-white/[0.04] dark:focus-within:border-blue-500/60">
        <textarea
          ref={inputRef}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          disabled={disabled || loading}
          rows={1}
          placeholder={disabled ? "Document is still processing…" : "Ask anything about your documents…"}
          className="max-h-40 min-h-[52px] w-full resize-none bg-transparent px-4 pt-3.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 disabled:cursor-not-allowed disabled:opacity-60 dark:text-white dark:placeholder:text-slate-500"
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              onSubmit();
            }
          }}
        />

        <div className="flex items-center justify-between gap-2 px-3 pb-3 pt-1">
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={onAttachClick}
              title="Attach a document"
              className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:text-slate-500 dark:hover:bg-white/5 dark:hover:text-slate-300"
            >
              <Paperclip className="h-4 w-4" />
            </button>
            <button
              type="button"
              title="Search the web (coming soon)"
              className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:text-slate-500 dark:hover:bg-white/5 dark:hover:text-slate-300"
            >
              <Globe className="h-4 w-4" />
            </button>
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setModeOpen((open) => !open)}
                className="flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
              >
                {mode}
                <ChevronDown className={`h-3.5 w-3.5 transition ${modeOpen ? "rotate-180" : ""}`} />
              </button>
              {modeOpen ? (
                <div className="absolute bottom-full left-0 z-20 mb-2 w-40 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-lg dark:border-white/10 dark:bg-[#12172a]">
                  {SEARCH_MODES.map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => {
                        setMode(option);
                        setModeOpen(false);
                      }}
                      className="block w-full px-3 py-2 text-left text-xs font-medium text-slate-600 transition hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-white/5"
                    >
                      {option}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              title="Smart suggestions (coming soon)"
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:border-white/10 dark:text-slate-500 dark:hover:bg-white/5 dark:hover:text-slate-300"
            >
              <Sparkles className="h-4 w-4" />
            </button>
            <button
              type="submit"
              disabled={disabled || loading || !value.trim()}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 dark:disabled:bg-white/10 dark:disabled:text-slate-600"
              aria-label="Send question"
            >
              <SendHorizontal className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </form>
  );
};

export default ChatInput;