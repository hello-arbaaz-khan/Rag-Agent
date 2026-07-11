import { useState } from "react";
import { X } from "lucide-react";
import { useAppContext } from "../../context/AppContext";
import { documentApi } from "../../services/api";
import FileDropzone from "./FileDropzone";
import Spinner from "../Common/Spinner";

const UploadModal = ({ open, onClose }) => {
  const { dispatch, addToast, loadDocuments } = useAppContext();
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const handleUpload = async () => {
    if (!file) {
      setError("Select a document before uploading.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("File size must be less than 50MB.");
      return;
    }

    setUploading(true);
    setError("");
    try {
      const document = await documentApi.uploadDocument(file, (event) => {
        if (!event.total) return;
        setProgress(Math.round((event.loaded * 100) / event.total));
      });
      dispatch({ type: "UPSERT_DOCUMENT", payload: document, select: true });
      
      // Reload documents to ensure frontend is synced with backend
      await new Promise(r => setTimeout(r, 500));
      await loadDocuments();
      
      addToast("Upload complete. Processing started.", "success");
      setFile(null);
      setProgress(0);
      onClose();
    } catch (uploadError) {
      setError(uploadError.message);
      addToast(uploadError.message, "error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/75 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg animate-fade-in rounded-xl border border-slate-700 bg-brand-card p-5 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-extrabold text-white">Upload document</h2>
            <p className="text-sm text-slate-400">Add a source file for the RAG agent.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white"
            aria-label="Close upload modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <FileDropzone file={file} setFile={setFile} />

        {uploading ? (
          <div className="mt-5">
            <div className="mb-2 flex items-center justify-between text-xs font-semibold text-slate-300">
              <span>Uploading</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-600 to-violet-600 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : null}

        {error ? (
          <div className="mt-4 rounded-xl border border-red-500/30 bg-red-950/30 p-3 text-sm text-red-100">
            {error}
          </div>
        ) : null}

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={uploading}
            className="rounded-xl border border-slate-600 px-4 py-2 text-sm font-bold text-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={uploading}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-700 px-4 py-2 text-sm font-bold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? <Spinner /> : null}
            Upload
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadModal;
