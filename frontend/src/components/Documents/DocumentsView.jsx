import { useState } from "react";
import { FileText, Search, UploadCloud } from "lucide-react";
import { useAppContext } from "../../context/AppContext";
import { documentApi } from "../../services/api";
import DocumentItem from "../Sidebar/DocumentItem";

const DocumentsView = ({ onUploadClick, onOpenInChat }) => {
  const { documents, loadingDocuments, apiError, selectedDocumentId, dispatch, addToast, loadDocuments } = useAppContext();
  const [query, setQuery] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const filtered = documents.filter((doc) => doc.name?.toLowerCase().includes(query.trim().toLowerCase()));

  const handleSelect = (documentId) => {
    dispatch({ type: "SET_SELECTED_DOCUMENT", payload: documentId });
    onOpenInChat?.();
  };

  const handleDelete = async (event, documentId) => {
    event.stopPropagation();
    setDeletingId(documentId);
    try {
      await documentApi.deleteDocument(documentId);
      dispatch({ type: "REMOVE_DOCUMENT", payload: documentId });
      addToast("Document deleted.", "success");
      await loadDocuments();
    } catch (err) {
      addToast(err.message, "error");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="mx-auto flex h-full max-w-5xl flex-col p-6 sm:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Documents</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {documents.length} file{documents.length === 1 ? "" : "s"} uploaded
          </p>
        </div>
        <button
          type="button"
          onClick={onUploadClick}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-blue-600/20 transition hover:from-blue-500 hover:to-indigo-500"
        >
          <UploadCloud className="h-4 w-4" />
          Upload document
        </button>
      </div>

      <div className="relative mt-5">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your documents…"
          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-3.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 dark:border-white/10 dark:bg-white/[0.03] dark:text-white dark:placeholder:text-slate-500"
        />
      </div>

      <div className="mt-5 min-h-0 flex-1 overflow-y-auto pb-6">
        {loadingDocuments ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {[0, 1, 2, 3].map((item) => (
              <div key={item} className="h-20 animate-pulse rounded-xl bg-slate-100 dark:bg-white/5" />
            ))}
          </div>
        ) : null}

        {!loadingDocuments && apiError ? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
            {apiError}
          </div>
        ) : null}

        {!loadingDocuments && !apiError && documents.length === 0 ? (
          <button
            type="button"
            onClick={onUploadClick}
            className="flex w-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center transition hover:border-blue-400 hover:bg-blue-50/40 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-blue-500/40 dark:hover:bg-blue-500/5"
          >
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-500 dark:bg-blue-500/10 dark:text-blue-300">
              <FileText className="h-6 w-6" />
            </div>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">No documents yet</p>
            <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">Upload a file to start chatting with it</p>
          </button>
        ) : null}

        {!loadingDocuments && filtered.length ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {filtered.map((document) => (
              <DocumentItem
                key={document.id}
                document={document}
                selected={document.id === selectedDocumentId}
                onSelect={() => handleSelect(document.id)}
                onDelete={(event) => handleDelete(event, document.id)}
              />
            ))}
          </div>
        ) : null}

        {!loadingDocuments && !apiError && documents.length > 0 && filtered.length === 0 ? (
          <p className="mt-6 text-center text-sm text-slate-400 dark:text-slate-500">No documents match "{query}".</p>
        ) : null}
      </div>
    </div>
  );
};

export default DocumentsView;