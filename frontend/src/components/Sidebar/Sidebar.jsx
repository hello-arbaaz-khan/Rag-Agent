import { BrainCircuit, FileWarning } from "lucide-react";
import { documentApi } from "../../services/api";
import { useAppContext } from "../../context/AppContext";
import DocumentItem from "./DocumentItem";
import UploadButton from "./UploadButton";

const SidebarSkeleton = () => (
  <div className="space-y-3">
    {[0, 1, 2].map((item) => (
      <div key={item} className="h-20 animate-pulse rounded-xl bg-slate-800/70" />
    ))}
  </div>
);

const Sidebar = ({ onUploadClick }) => {
  const {
    documents,
    selectedDocumentId,
    loadingDocuments,
    apiError,
    dispatch,
    addToast
  } = useAppContext();

  const handleDelete = async (document) => {
    try {
      await documentApi.deleteDocument(document.id);
      dispatch({ type: "REMOVE_DOCUMENT", payload: document.id });
      addToast("Document deleted.", "success");
    } catch (error) {
      addToast(error.message, "error");
    }
  };

  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-800 bg-slate-950/80 p-4 lg:w-96">
      <div className="mb-6 flex items-center gap-3">
        <div className="rounded-xl bg-gradient-to-br from-blue-700 to-violet-700 p-2.5 shadow-lg shadow-blue-950/40">
          <BrainCircuit className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-extrabold text-white">DocuMind AI</h1>
          <p className="text-xs font-medium text-slate-400">RAG document assistant</p>
        </div>
      </div>

      <UploadButton onClick={onUploadClick} />

      <div className="mt-6 flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wide text-slate-300">Documents</h2>
        <span className="rounded-full bg-slate-800 px-2.5 py-1 text-xs font-bold text-slate-300">
          {documents.length} total
        </span>
      </div>

      <div className="mt-4 min-h-0 flex-1 overflow-y-auto pr-1">
        {loadingDocuments ? <SidebarSkeleton /> : null}

        {!loadingDocuments && apiError ? (
          <div className="rounded-xl border border-red-500/30 bg-red-950/30 p-4 text-sm text-red-100">
            <div className="mb-2 flex items-center gap-2 font-bold">
              <FileWarning className="h-4 w-4" />
              API unavailable
            </div>
            <p className="text-red-200/90">{apiError}</p>
          </div>
        ) : null}

        {!loadingDocuments && !apiError && documents.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 bg-slate-900/50 p-5 text-center">
            <p className="text-sm font-semibold text-white">No documents uploaded yet.</p>
            <p className="mt-1 text-xs text-slate-400">Upload a PDF, TXT, or DOCX to start asking questions.</p>
          </div>
        ) : null}

        <div className="space-y-3">
          {documents.map((document) => (
            <DocumentItem
              key={document.id}
              document={document}
              selected={document.id === selectedDocumentId}
              onSelect={() => dispatch({ type: "SET_SELECTED_DOCUMENT", payload: document.id })}
              onDelete={() => handleDelete(document)}
            />
          ))}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
