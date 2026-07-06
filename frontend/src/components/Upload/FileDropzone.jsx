import { FileArchive, UploadCloud, X } from "lucide-react";

const formatSize = (bytes) => {
  if (!bytes) return "0 MB";
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const FileDropzone = ({ file, setFile }) => {
  const handleFile = (selectedFile) => {
    if (selectedFile) setFile(selectedFile);
  };

  return (
    <div
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        handleFile(event.dataTransfer.files?.[0]);
      }}
      className="rounded-xl border-2 border-dashed border-slate-600 bg-slate-950/50 p-6 text-center transition hover:border-blue-500 hover:bg-slate-900"
    >
      <input
        id="file-upload"
        type="file"
        accept=".pdf,.txt,.doc,.docx"
        className="sr-only"
        onChange={(event) => handleFile(event.target.files?.[0])}
      />
      {!file ? (
        <label htmlFor="file-upload" className="block cursor-pointer">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-blue-600/15 text-blue-200">
            <UploadCloud className="h-7 w-7" />
          </div>
          <p className="text-sm font-bold text-white">Drop your document here or browse</p>
          <p className="mt-2 text-xs text-slate-400">Supported formats: PDF, TXT, DOCX. Max size: 50MB.</p>
        </label>
      ) : (
        <div className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-900 p-4 text-left">
          <div className="rounded-xl bg-violet-600/15 p-3 text-violet-200">
            <FileArchive className="h-6 w-6" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold text-white">{file.name}</p>
            <p className="mt-1 text-xs text-slate-400">
              {formatSize(file.size)} - {file.name.split(".").pop()?.toUpperCase()}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setFile(null)}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white"
            aria-label="Remove selected file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default FileDropzone;
