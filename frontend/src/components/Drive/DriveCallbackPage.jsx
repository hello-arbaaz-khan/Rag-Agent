import { useEffect, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";

/**
 * Rendered when the URL has ?drive_status=connected|error — i.e. right
 * after Google's OAuth redirect bounces through drive_service's /callback.
 * This is what the OAuth popup shows. It immediately notifies the opener
 * window (the main app) via postMessage so the UI there updates without
 * waiting on polling, then offers to close itself.
 */
const DriveCallbackPage = () => {
  const [autoCloseFailed, setAutoCloseFailed] = useState(false);

  const params = new URLSearchParams(window.location.search);
  const status = params.get("drive_status");
  const email = params.get("email");
  const message = params.get("message");
  const isSuccess = status === "connected";

  useEffect(() => {
    if (window.opener) {
      window.opener.postMessage(
        { source: "drive-oauth-callback", status, email, message },
        window.location.origin
      );
    }

    const timer = window.setTimeout(() => {
      if (window.opener) {
        window.close();
        // If we're still here a moment after calling close(), the browser
        // blocked it — fall back to showing a manual "close" prompt.
        window.setTimeout(() => setAutoCloseFailed(true), 300);
      }
    }, 900);

    return () => window.clearTimeout(timer);
  }, [status, email, message]);

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-white p-6 text-center dark:bg-brand-bg">
      <div className="max-w-sm">
        {isSuccess ? (
          <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
        ) : (
          <XCircle className="mx-auto h-12 w-12 text-red-500" />
        )}
        <h1 className="mt-4 text-lg font-bold text-slate-900 dark:text-white">
          {isSuccess ? "Google Drive connected" : "Connection failed"}
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {isSuccess
            ? email
              ? `Connected as ${email}.`
              : "Your Google Drive is now connected."
            : message || "Something went wrong while connecting Google Drive."}
        </p>
        {window.opener ? (
          <p className="mt-4 text-xs text-slate-400 dark:text-slate-500">
            {autoCloseFailed ? (
              <button
                type="button"
                onClick={() => window.close()}
                className="font-semibold text-blue-600 hover:underline dark:text-blue-400"
              >
                Close this window
              </button>
            ) : (
              "This window will close automatically…"
            )}
          </p>
        ) : (
          <a href="/" className="mt-4 inline-block text-sm font-semibold text-blue-600 hover:underline dark:text-blue-400">
            Continue to app
          </a>
        )}
      </div>
    </div>
  );
};

export default DriveCallbackPage;
