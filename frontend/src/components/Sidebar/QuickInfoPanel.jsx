import { Database, FileText, ShieldCheck, Sparkles, X } from "lucide-react";
import { useAppContext } from "../../context/AppContext";

const FILE_TYPES = [
  { label: "PDF", ext: "pdf", classes: "bg-red-500/15 text-red-500 dark:text-red-300" },
  { label: "DOCX", ext: "docx", classes: "bg-blue-500/15 text-blue-500 dark:text-blue-300" },
  { label: "TXT", ext: "txt", classes: "bg-slate-500/15 text-slate-500 dark:text-slate-300" },
  { label: "PPTX", ext: "pptx", classes: "bg-orange-500/15 text-orange-500 dark:text-orange-300" },
  { label: "XLSX", ext: "xlsx", classes: "bg-emerald-500/15 text-emerald-500 dark:text-emerald-300" },
  { label: "MD", ext: "md", classes: "bg-violet-500/15 text-violet-500 dark:text-violet-300" }
];

// A generous soft cap just to give the storage bar something to render
// against — the backend has no plan/quota concept yet.
const STORAGE_CAP_GB = 12;

const formatGb = (bytes) => (bytes / (1024 * 1024 * 1024)).toFixed(bytes >= 1024 * 1024 * 1024 ? 1 : 2);

const QuickInfoPanel = ({ onClose, onNavigate = () => {} }) => {
  const { documents } = useAppContext();
  const totalBytes = documents.reduce((sum, doc) => sum + (doc.file_size || 0), 0);
  const usedGb = formatGb(totalBytes);
  const usedPct = Math.min(100, (totalBytes / (STORAGE_CAP_GB * 1024 * 1024 * 1024)) * 100);

  return (
    <aside className="flex h-full w-full flex-col overflow-y-auto border-l border-slate-200 bg-white p-5 dark:border-white/5 dark:bg-[#0b0f19] lg:w-[320px]">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-bold text-slate-900 dark:text-white">Quick Info</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close quick info"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 dark:hover:bg-white/5"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-3">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/5 dark:bg-white/[0.02]">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-500/15 text-blue-500 dark:text-blue-300">
              <FileText className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-blue-600 dark:text-blue-300">Documents</p>
              <p className="mt-0.5 text-sm font-bold text-slate-800 dark:text-white">{documents.length} files uploaded</p>
              <button
                type="button"
                onClick={() => onNavigate("documents")}
                className="mt-1 text-xs font-semibold text-blue-600 hover:underline dark:text-blue-400"
              >
                View all →
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/5 dark:bg-white/[0.02]">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-500/15 text-violet-500 dark:text-violet-300">
              <Database className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-violet-600 dark:text-violet-300">Storage</p>
              <p className="mt-0.5 text-sm font-bold text-slate-800 dark:text-white">{usedGb} GB used</p>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-white/10">
                <div className="h-full rounded-full bg-blue-500" style={{ width: `${usedPct}%` }} />
              </div>
              <p className="mt-1 text-right text-[11px] text-slate-400 dark:text-slate-500">{STORAGE_CAP_GB} GB total</p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/5 dark:bg-white/[0.02]">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-500 dark:text-emerald-300">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-300">RAG Agent</p>
              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
                Searches your documents, provides accurate answers with sources.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-5">
        <h3 className="text-xs font-bold uppercase tracking-wide text-slate-400 dark:text-slate-500">Supported File Types</h3>
        <div className="mt-2.5 grid grid-cols-2 gap-2">
          {FILE_TYPES.map((type) => (
            <div
              key={type.ext}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/5 dark:bg-white/[0.02]"
            >
              <span className={`flex h-6 w-6 items-center justify-center rounded-md text-[10px] font-bold ${type.classes}`}>
                {type.label.slice(0, 1)}
              </span>
              <span className="text-xs font-medium text-slate-600 dark:text-slate-300">{type.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-5 overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 p-5 text-white">
        <Sparkles className="h-6 w-6" />
        <h3 className="mt-3 text-base font-bold leading-tight">Smarter Answers From Your Documents</h3>
        <p className="mt-2 text-xs leading-5 text-blue-100">
          Upload, search, and chat with your files using advanced RAG technology.
        </p>
      </div>
    </aside>
  );
};

export default QuickInfoPanel;