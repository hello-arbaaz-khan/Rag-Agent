import { CheckCircle2, HardDrive, Loader2 } from "lucide-react";
import { useDriveConnection } from "../../hooks/useDriveConnection";

const DriveConnection = () => {
  const { loading, connected, googleEmail, connecting, disconnecting, connect, disconnect } = useDriveConnection();

  return (
    <div className="w-full max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-slate-900/10 dark:border-white/10 dark:bg-brand-card">
      <div className="flex flex-col gap-5 p-8 sm:flex-row sm:items-center sm:justify-between sm:p-10">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-300">
            <HardDrive className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Google Drive</h2>
            <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
              Connect Google Drive to automatically sync and index your files for chat and search.
            </p>

            {loading ? (
              <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">Checking connection…</p>
            ) : connected ? (
              <div className="mt-3 flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Connected{googleEmail ? ` as ${googleEmail}` : ""}
              </div>
            ) : (
              <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">Not connected</p>
            )}
          </div>
        </div>

        <div className="shrink-0">
          {loading ? null : connected ? (
            <button
              type="button"
              onClick={disconnect}
              disabled={disconnecting}
              className="flex items-center gap-2 rounded-xl border border-red-200 px-4 py-2.5 text-sm font-semibold text-red-500 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-500/20 dark:text-red-300 dark:hover:bg-red-500/10"
            >
              {disconnecting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {disconnecting ? "Disconnecting…" : "Disconnect"}
            </button>
          ) : (
            <button
              type="button"
              onClick={connect}
              disabled={connecting}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {connecting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {connecting ? "Connecting…" : "Connect Drive"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DriveConnection;
