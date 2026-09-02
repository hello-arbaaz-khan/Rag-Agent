import { HardDrive } from "lucide-react";
import { useDriveConnection } from "../../hooks/useDriveConnection";

/**
 * Small always-visible indicator in the sidebar footer. Doesn't connect or
 * disconnect by itself — clicking it just takes you to Settings, which owns
 * the actual Connect/Disconnect action (avoids duplicating the OAuth popup
 * flow in two places).
 */
const DriveStatusBadge = ({ onNavigate = () => {} }) => {
  const { loading, connected } = useDriveConnection();

  if (loading) return null;

  return (
    <button
      type="button"
      onClick={() => onNavigate("settings")}
      title={connected ? "Google Drive connected" : "Connect Google Drive"}
      className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs font-medium text-slate-500 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5"
    >
      <HardDrive className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{connected ? "Drive connected" : "Connect Google Drive"}</span>
      <span
        className={`ml-auto h-1.5 w-1.5 shrink-0 rounded-full ${
          connected ? "bg-emerald-500" : "bg-slate-300 dark:bg-slate-600"
        }`}
      />
    </button>
  );
};

export default DriveStatusBadge;
