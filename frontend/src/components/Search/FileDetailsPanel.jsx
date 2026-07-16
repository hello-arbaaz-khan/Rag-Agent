import { useState } from "react";
import { Copy, Check, FileText, MessageSquare, Info } from "lucide-react";
import { mimeToLabel, syncStatusStyles, timeAgo } from "./searchUtils";

const DetailRow = ({ label, value, mono = false }) => (
  <div className="flex items-center justify-between gap-3 border-b border-slate-800/70 py-3 last:border-b-0">
    <span className="text-sm text-slate-400">{label}</span>
    <span className={`truncate text-right text-sm font-medium text-white ${mono ? "font-mono text-xs" : ""}`}>
      {value ?? "—"}
    </span>
  </div>
);

const FileDetailsPanel = ({ result, onOpenInChat }) => {
  const [copied, setCopied] = useState(false);

  if (!result) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/40 p-8 text-center">
        <div className="mb-3 rounded-xl bg-slate-800 p-3 text-slate-400">
          <Info className="h-6 w-6" />
        </div>
        <p className="text-sm font-semibold text-white">Select a result</p>
        <p className="mt-1 text-xs text-slate-500">Choose a search result to see its file details.</p>
      </div>
    );
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.drive_file_id || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard not available, ignore
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40">
      <div className="flex items-center justify-between border-b border-slate-800 p-4">
        <h3 className="text-sm font-bold text-white">File Details</h3>
        <button
          type="button"
          onClick={() => onOpenInChat(result)}
          disabled={!result.document_id}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <MessageSquare className="h-3.5 w-3.5" />
          Open in Chat
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <div className="mb-4 flex items-start gap-3">
          <div className="rounded-xl bg-slate-800 p-3 text-red-400">
            <FileText className="h-6 w-6" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-base font-bold text-white">{result.name}</p>
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full border px-2 py-0.5 text-xs font-semibold capitalize ${
                  syncStatusStyles[result.sync_status] || "border-slate-500/40 bg-slate-700/60 text-slate-200"
                }`}
              >
                {result.sync_status || "unknown"}
              </span>
              <span className="rounded-full border border-slate-600 bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300">
                {mimeToLabel(result.mime_type)} Document
              </span>
              {result.document_id ? (
                <span className="rounded-full border border-slate-600 bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300">
                  Document ID: {result.document_id}
                </span>
              ) : null}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/40 px-4">
          <div className="flex items-center justify-between gap-3 border-b border-slate-800/70 py-3">
            <span className="text-sm text-slate-400">Drive File ID</span>
            <div className="flex min-w-0 items-center gap-2">
              <span className="truncate font-mono text-xs font-medium text-white">{result.drive_file_id}</span>
              <button
                type="button"
                onClick={handleCopy}
                className="shrink-0 rounded-md p-1 text-slate-400 transition hover:bg-slate-800 hover:text-white"
                aria-label="Copy Drive File ID"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>
          <DetailRow label="Name" value={result.name} />
          <DetailRow label="MIME Type" value={result.mime_type} mono />
          <DetailRow
            label="Drive Modified At"
            value={result.drive_modified_at ? new Date(result.drive_modified_at).toLocaleString() : "—"}
          />
          <DetailRow
            label="Sync Status"
            value={<span className="capitalize">{result.sync_status || "—"}</span>}
          />
          <DetailRow label="Document ID" value={result.document_id ?? "—"} />
          {typeof result.relevance_score === "number" ? (
            <DetailRow label="Relevance Score" value={result.relevance_score.toFixed(4)} />
          ) : null}
        </div>

        {result.matched_snippet ? (
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <p className="mb-2 text-sm font-bold text-white">Matched Snippet Preview</p>
            <p className="text-sm leading-6 text-slate-300">{result.matched_snippet}</p>
          </div>
        ) : null}

        <div className="mt-4 flex items-start gap-2 rounded-xl border border-blue-500/20 bg-blue-950/20 p-3">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-300" />
          <p className="text-xs text-blue-200/90">
            Relevance score indicates how well this document matches your search query.
          </p>
        </div>

        <p className="mt-3 text-xs text-slate-500">Last synced {timeAgo(result.drive_modified_at)}</p>
      </div>
    </div>
  );
};

export default FileDetailsPanel;
