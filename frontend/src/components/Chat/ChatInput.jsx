import { SendHorizontal } from "lucide-react";

const ChatInput = ({ value, setValue, onSubmit, disabled, loading }) => (
  <form
    onSubmit={(event) => {
      event.preventDefault();
      onSubmit();
    }}
    className="flex items-end gap-3 border-t border-slate-800 bg-slate-950/80 p-4"
  >
    <textarea
      value={value}
      onChange={(event) => setValue(event.target.value)}
      disabled={disabled || loading}
      rows={1}
      placeholder={disabled ? "Document is still processing..." : "Ask anything about this document..."}
      className="max-h-32 min-h-12 flex-1 resize-none rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
      onKeyDown={(event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          onSubmit();
        }
      }}
    />
    <button
      type="submit"
      disabled={disabled || loading || !value.trim()}
      className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-700 text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
      aria-label="Send question"
    >
      <SendHorizontal className="h-5 w-5" />
    </button>
  </form>
);

export default ChatInput;
