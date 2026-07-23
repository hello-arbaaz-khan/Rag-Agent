import { useEffect, useMemo, useRef, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  Download,
  ExternalLink,
  FileText,
  Filter as FilterIcon,
  MoreVertical,
  RotateCcw,
  Search,
  X
} from "lucide-react";
import { documentApi } from "../../services/api";
import { useAppContext } from "../../context/AppContext";
import FileDetailsPanel from "./FileDetailsPanel";
import { mimeToLabel, syncStatusStyles } from "./searchUtils";
import {
  addSearchHistory,
  clearSearchHistory,
  getSearchHistory,
  removeSearchHistory
} from "./Searchhistory.js";

const PAGE_SIZE_OPTIONS = [10, 20, 50];

const AdvancedSearch = ({ onOpenInChat }) => {
  const { addToast } = useAppContext();

  const [query, setQuery] = useState("");
  const [allResults, setAllResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const [docType, setDocType] = useState("all");
  const [syncStatus, setSyncStatus] = useState("all");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [openMenuId, setOpenMenuId] = useState(null);
  const [detailsResult, setDetailsResult] = useState(null);

  const [recentSearches, setRecentSearches] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const searchBarRef = useRef(null);

  useEffect(() => {
    setRecentSearches(getSearchHistory());
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchBarRef.current && !searchBarRef.current.contains(event.target)) {
        setShowHistory(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const visibleHistory = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return recentSearches;
    return recentSearches.filter((item) => item.toLowerCase().includes(q));
  }, [recentSearches, query]);

  const runSearch = async (searchQuery) => {
    setLoading(true);
    try {
      const data = await documentApi.search(searchQuery);
      setAllResults(data.results || []);
      setPage(1);
    } catch (error) {
      addToast(error.message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSearch("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed) setRecentSearches(addSearchHistory(trimmed));
    setShowHistory(false);
    runSearch(trimmed);
  };

  const handleReset = () => {
    setQuery("");
    setDocType("all");
    setSyncStatus("all");
    setFromDate("");
    setToDate("");
    runSearch("");
  };

  const handleSelectHistory = (term) => {
    setQuery(term);
    setRecentSearches(addSearchHistory(term));
    setShowHistory(false);
    runSearch(term);
  };


  const handleRemoveHistoryItem = (term, event) => {
    event.stopPropagation();
    setRecentSearches(removeSearchHistory(term));
  };

  const handleClearHistory = () => {
    setRecentSearches(clearSearchHistory());
  };



  const handleExport = () => {
    const rows = filteredResults.map((r) => ({
      drive_file_id: r.drive_file_id,
      name: r.name,
      mime_type: r.mime_type,
      drive_modified_at: r.drive_modified_at,
      sync_status: r.sync_status,
      document_id: r.document_id,
      total_chunks: r.total_chunks
    }));
    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "documind-search-results.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  const docTypeOptions = useMemo(() => {
    const labels = new Set(allResults.map((r) => mimeToLabel(r.mime_type)));
    return ["all", ...Array.from(labels).sort()];
  }, [allResults]);

  const filteredResults = useMemo(() => {
    return allResults.filter((r) => {
      if (docType !== "all" && mimeToLabel(r.mime_type) !== docType) return false;
      if (syncStatus !== "all" && r.sync_status !== syncStatus) return false;

      if (fromDate && r.drive_modified_at) {
        if (new Date(r.drive_modified_at) < new Date(fromDate)) return false;
      }
      if (toDate && r.drive_modified_at) {
        const end = new Date(toDate);
        end.setHours(23, 59, 59, 999);
        if (new Date(r.drive_modified_at) > end) return false;
      }
      return true;
    });
  }, [allResults, docType, syncStatus, fromDate, toDate]);

  const totalPages = Math.max(1, Math.ceil(filteredResults.length / pageSize));
  const startIdx = (page - 1) * pageSize;
  const pageResults = filteredResults.slice(startIdx, startIdx + pageSize);

  useEffect(() => {
    if (page > totalPages) setPage(1);
  }, [totalPages, page]);

  const formatDateTime = (value) => {
    if (!value) return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return "—";
    const pad = (n) => String(n).padStart(2, "0");
    return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}, ${pad(d.getHours())}:${pad(
      d.getMinutes()
    )}:${pad(d.getSeconds())}`;
  };

  return (
    <div className="flex h-full flex-col overflow-hidden bg-brand-bg p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Advanced Search</h1>
          <p className="mt-1 text-sm text-slate-400">Search across all your documents with AI-powered intelligence</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mb-4 flex items-center gap-3">
        <div ref={searchBarRef} className="relative flex-1">
          <div className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-3">
            <Search className="h-4 w-4 shrink-0 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setShowHistory(true)}
              placeholder="Search by file name, content, keyword, or ask a question..."
              className="w-full bg-transparent text-sm text-white placeholder:text-slate-500 focus:outline-none"
            />
          </div>

          {showHistory && visibleHistory.length > 0 ? (
            <div className="absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Recent searches
                </span>
                <button
                  type="button"
                  onClick={handleClearHistory}
                  className="text-xs font-medium text-slate-400 hover:text-white"
                >
                  Clear all
                </button>
              </div>
              <ul className="max-h-64 overflow-y-auto">
                {visibleHistory.map((term) => (
                  <li key={term} className="flex items-center justify-between gap-1 px-2 py-1">
                    <button
                      type="button"
                      onClick={() => handleSelectHistory(term)}
                      className="flex flex-1 items-center gap-2 truncate rounded-lg px-2 py-1.5 text-left text-sm text-slate-200 hover:bg-slate-800"
                    >
                      <Clock className="h-3.5 w-3.5 shrink-0 text-slate-500" />
                      <span className="truncate">{term}</span>
                    </button>
                    <button
                      type="button"
                      onClick={(e) => handleRemoveHistoryItem(term, e)}
                      className="shrink-0 rounded p-1 text-slate-500 hover:bg-slate-700 hover:text-white"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-blue-700 to-violet-700 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-blue-950/30 transition hover:brightness-110 disabled:opacity-60"
        >
          <Search className="h-4 w-4" />
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      <div className="mb-5 flex flex-wrap items-center gap-3">
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-200 focus:outline-none"
        >
          {docTypeOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt === "all" ? "All Document Types" : opt}
            </option>
          ))}
        </select>

        <select
          value={syncStatus}
          onChange={(e) => setSyncStatus(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-200 focus:outline-none"
        >
          <option value="all">All Sync Status</option>
          <option value="indexed">Indexed</option>
          <option value="processing">Processing</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>

        <input
          type="date"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-200 focus:outline-none"
        />
        <input
          type="date"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-200 focus:outline-none"
        />

        <button
          type="button"
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm font-semibold text-slate-300 transition hover:bg-slate-800"
        >
          <FilterIcon className="h-3.5 w-3.5" />
          Filter
        </button>

        <button
          type="button"
          onClick={handleReset}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm font-semibold text-slate-300 transition hover:bg-slate-800"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Reset
        </button>
      </div>

      <div className="flex min-h-0 flex-1 flex-col rounded-2xl border border-slate-800 bg-slate-900/40">
        <div className="flex items-center justify-between border-b border-slate-800 p-4">
          <h2 className="text-sm font-bold text-white">
            All Documents <span className="text-slate-400">({filteredResults.length})</span>
          </h2>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-xs font-bold text-slate-200 transition hover:bg-slate-800"
          >
            <Download className="h-3.5 w-3.5" />
            Export
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-900/95 text-xs uppercase tracking-wide text-slate-400 backdrop-blur">
              <tr>
                <th className="px-4 py-3 font-semibold">Drive ID</th>
                <th className="px-4 py-3 font-semibold">Name</th>
                <th className="px-4 py-3 font-semibold">Mime Type</th>
                <th className="px-4 py-3 font-semibold">Drive Modified At</th>
                <th className="px-4 py-3 font-semibold">Sync Status</th>
                <th className="px-4 py-3 font-semibold">Document ID</th>
                <th className="px-4 py-3 font-semibold">Chunks</th>
                <th className="px-4 py-3 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-slate-400">
                    Loading documents...
                  </td>
                </tr>
              ) : null}

              {!loading && pageResults.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-slate-400">
                    No documents found. Try a different query or adjust your filters.
                  </td>
                </tr>
              ) : null}

              {!loading &&
                pageResults.map((r) => (
                  <tr
                    key={`${r.document_id || "nodoc"}-${r.drive_file_id}`}
                    className="border-t border-slate-800/70 transition hover:bg-slate-800/40"
                  >
                    <td className="max-w-[160px] truncate px-4 py-3 font-mono text-xs text-slate-400">
                      {r.drive_file_id}
                    </td>
                    <td className="max-w-[240px] px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 shrink-0 text-slate-400" />
                        <span className="truncate font-medium text-white">{r.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-md bg-slate-800 px-2 py-0.5 text-xs font-bold text-slate-300">
                        {mimeToLabel(r.mime_type)}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-300">{formatDateTime(r.drive_modified_at)}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold capitalize ${
                          syncStatusStyles[r.sync_status] || "border-slate-500/40 bg-slate-700/60 text-slate-200"
                        }`}
                      >
                        {r.sync_status || "unknown"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{r.document_id ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {typeof r.total_chunks === "number" ? (
                        <span className="inline-flex rounded-md bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300">
                          {r.total_chunks}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="relative flex items-center justify-end gap-1">
                        <button
                          type="button"
                          title="Open in chat"
                          onClick={() => onOpenInChat(r)}
                          disabled={!r.document_id}
                          className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          title="More actions"
                          onClick={() =>
                            setOpenMenuId(openMenuId === r.drive_file_id ? null : r.drive_file_id)
                          }
                          className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </button>

                        {openMenuId === r.drive_file_id ? (
                          <div className="absolute right-0 top-9 z-20 w-40 rounded-lg border border-slate-700 bg-slate-900 py-1 shadow-xl">
                            <button
                              type="button"
                              onClick={() => {
                                setDetailsResult(r);
                                setOpenMenuId(null);
                              }}
                              className="block w-full px-3 py-2 text-left text-xs font-medium text-slate-200 hover:bg-slate-800"
                            >
                              View Details
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                onOpenInChat(r);
                                setOpenMenuId(null);
                              }}
                              disabled={!r.document_id}
                              className="block w-full px-3 py-2 text-left text-xs font-medium text-slate-200 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                              Open in Chat
                            </button>
                          </div>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 p-4">
          <p className="text-xs text-slate-400">
            {filteredResults.length === 0
              ? "Showing 0 documents"
              : `Showing ${startIdx + 1} to ${Math.min(startIdx + pageSize, filteredResults.length)} of ${
                  filteredResults.length
                } documents`}
          </p>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-lg border border-slate-700 p-1.5 text-slate-300 transition hover:bg-slate-800 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="rounded-lg border border-blue-500/70 bg-blue-950/50 px-3 py-1 text-xs font-bold text-white">
                {page}
              </span>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="rounded-lg border border-slate-700 p-1.5 text-slate-300 transition hover:bg-slate-800 disabled:opacity-40"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>

            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="rounded-lg border border-slate-700 bg-slate-900/60 px-2 py-1.5 text-xs font-semibold text-slate-200 focus:outline-none"
            >
              {PAGE_SIZE_OPTIONS.map((size) => (
                <option key={size} value={size}>
                  {size} / page
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {detailsResult ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4">
          <div className="max-h-[85vh] w-full max-w-lg overflow-hidden">
            <div className="relative">
              <button
                type="button"
                onClick={() => setDetailsResult(null)}
                className="absolute -top-2 -right-2 z-10 rounded-full bg-slate-800 p-1.5 text-slate-300 hover:bg-slate-700 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
              <FileDetailsPanel
                result={detailsResult}
                onOpenInChat={(r) => {
                  setDetailsResult(null);
                  onOpenInChat(r);
                }}
              />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default AdvancedSearch;