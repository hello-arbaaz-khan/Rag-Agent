import { CheckCircle2, FileText, Trash2, TriangleAlert } from "lucide-react";
import Badge from "../Common/Badge";
import Spinner from "../Common/Spinner";

const DocumentItem = ({ document, selected, onSelect, onDelete }) => {
  const isProcessed = Boolean(document.is_processed);
  const hasError = Boolean(document.processing_error);

  return (
    <div
      className={`group w-full rounded-xl border p-3 text-left transition ${
        selected
          ? "border-blue-500/70 bg-blue-950/50 shadow-lg shadow-blue-950/20"
          : "border-slate-700/70 bg-slate-900/45 hover:border-slate-500 hover:bg-slate-800/70"
      }`}
    >
      <div className="flex items-start gap-3">
        <button type="button" onClick={onSelect} className="flex min-w-0 flex-1 items-start gap-3 text-left">
          <div className="mt-0.5 rounded-lg bg-slate-800 p-2 text-slate-300">
            <FileText className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-white">{document.name}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge className="uppercase">{document.file_type || "file"}</Badge>
              {hasError ? (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-red-300">
                  <TriangleAlert className="h-3.5 w-3.5" />
                  Error
                </span>
              ) : isProcessed ? (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-300">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Ready
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-200">
                  <Spinner className="h-3.5 w-3.5" />
                  Processing
                </span>
              )}
            </div>
          </div>
        </button>
        <button
          type="button"
          onClick={onDelete}
          className="rounded-lg p-1.5 text-slate-500 opacity-100 transition hover:bg-red-500/15 hover:text-red-300 sm:opacity-0 sm:group-hover:opacity-100"
          aria-label={`Delete ${document.name}`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default DocumentItem;
