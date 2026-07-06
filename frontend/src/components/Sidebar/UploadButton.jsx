import { UploadCloud } from "lucide-react";

const UploadButton = ({ onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-700 to-violet-700 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-950/40 transition hover:from-blue-600 hover:to-violet-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
  >
    <UploadCloud className="h-4 w-4" />
    Upload Document
  </button>
);

export default UploadButton;
