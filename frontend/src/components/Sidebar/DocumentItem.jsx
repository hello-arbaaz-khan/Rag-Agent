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
          ? "border-blue-400 bg-blue-50 shadow-sm dark:border-blue-500/70 dark:bg-blue-950/50 dark:shadow-lg dark:shadow-blue-950/20"
          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-white/20 dark:hover:bg-white/[0.05]"
      }`}
    >
      <div className="flex items-start gap-3">
        <button type="button" onClick={onSelect} className="flex min-w-0 flex-1 items-start gap-3 text-left">
          <div className="mt-0.5 rounded-lg bg-slate-100 p-2 text-slate-500 dark:bg-white/5 dark:text-slate-300">
            <FileText className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-800 dark:text-white">{document.name}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge className="uppercase">{document.file_type || "file"}</Badge>
              {hasError ? (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-red-500 dark:text-red-300">
                  <TriangleAlert className="h-3.5 w-3.5" />
                  Error
                </span>
              ) : isProcessed ? (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-300">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Ready
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-500 dark:text-blue-200">
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
          className="rounded-lg p-1.5 text-slate-400 opacity-100 transition hover:bg-red-50 hover:text-red-500 dark:text-slate-500 dark:hover:bg-red-500/15 dark:hover:text-red-300 sm:opacity-0 sm:group-hover:opacity-100"
          aria-label={`Delete ${document.name}`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default DocumentItem;