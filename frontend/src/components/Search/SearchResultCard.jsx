import { FileText } from "lucide-react";
import { mimeToLabel, relevanceTone, timeAgo } from "./searchUtils";

const SearchResultCard = ({ result, selected, onSelect }) => {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-xl border p-4 text-left transition ${
        selected
          ? "border-blue-500/70 bg-blue-950/40 shadow-lg shadow-blue-950/20"
          : "border-slate-700/70 bg-slate-900/45 hover:border-slate-500 hover:bg-slate-800/60"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <div className="mt-0.5 rounded-lg bg-slate-800 p-1.5 text-slate-300">
            <FileText className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">{result.name}</p>
            <span className="mt-1 inline-flex rounded-md bg-slate-800 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-300">
              {mimeToLabel(result.mime_type)}
            </span>
          </div>
        </div>
        {typeof result.relevance_score === "number" ? (
          <span
            className={`shrink-0 rounded-full border px-2 py-0.5 text-xs font-bold ${relevanceTone(
              result.relevance_score
            )}`}
          >
            {result.relevance_score.toFixed(4)}
          </span>
        ) : null}
      </div>

      {result.matched_snippet ? (
        <p className="mt-2 truncate text-xs text-slate-400">{result.matched_snippet}</p>
      ) : null}

      <p className="mt-2 text-xs text-slate-500">{timeAgo(result.drive_modified_at)}</p>
    </button>
  );
};

export default SearchResultCard;
