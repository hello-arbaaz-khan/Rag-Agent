import { useCallback, useEffect, useRef, useState } from "react";
import { driveApi } from "../services/api";
import { useAppContext } from "../context/AppContext";

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 3 * 60 * 1000; // give up after 3 minutes

/**
 * Shared Google Drive connection state, used by both the Settings card and
 * the Sidebar status badge so they always agree on connected/connecting/etc.
 *
 * Connect flow:
 *  1. Ask the backend for a Google auth_url, open it in a popup.
 *  2. The popup finishes on Google's side, which redirects the browser to
 *     drive_service's /callback, which 302s to `${FRONTEND_BASE_URL}/?drive_status=...`.
 *  3. Once that page loads in the popup, DriveCallbackPage posts a message
 *     back to `window.opener` — this hook listens for it and resolves
 *     immediately. A status-polling fallback covers popup blockers or
 *     postMessage getting lost.
 */
export const useDriveConnection = () => {
  const { addToast } = useAppContext();
  const [status, setStatus] = useState({ loading: true, connected: false, googleEmail: null });
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const popupRef = useRef(null);
  const pollTimerRef = useRef(null);
  const pollDeadlineRef = useRef(null);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await driveApi.status();
      setStatus({ loading: false, connected: !!data.connected, googleEmail: data.google_email ?? null });
      return data;
    } catch (error) {
      setStatus({ loading: false, connected: false, googleEmail: null });
      throw error;
    }
  }, []);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const finishConnectAttempt = useCallback(
    (result) => {
      stopPolling();
      setConnecting(false);
      if (popupRef.current && !popupRef.current.closed) {
        popupRef.current.close();
      }
      popupRef.current = null;

      if (result?.status === "connected") {
        addToast(result.email ? `Google Drive connected as ${result.email}.` : "Google Drive connected.", "success");
        refreshStatus();
      } else if (result?.status === "error") {
        addToast(result.message || "Google Drive connection failed.", "error");
      }
    },
    [addToast, refreshStatus, stopPolling]
  );

  // Listen for the postMessage the popup sends once it lands on
  // /?drive_status=... (see DriveCallbackPage).
  useEffect(() => {
    const handleMessage = (event) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.source !== "drive-oauth-callback") return;
      finishConnectAttempt(event.data);
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [finishConnectAttempt]);

  useEffect(() => {
    refreshStatus().catch(() => {});
  }, [refreshStatus]);

  useEffect(() => stopPolling, [stopPolling]);

  const connect = useCallback(async () => {
    if (connecting) return;
    setConnecting(true);

    const popup = window.open("", "google-drive-oauth", "width=520,height=680");

    try {
      const { auth_url: authUrl } = await driveApi.connect();
      if (popup) {
        popup.location.href = authUrl;
        popupRef.current = popup;
      } else {
        addToast("Please allow pop-ups to connect Google Drive.", "error");
        setConnecting(false);
        return;
      }
    } catch (error) {
      popup?.close();
      setConnecting(false);
      addToast(error.message || "Unable to start Google Drive connection.", "error");
      return;
    }

    // Fallback in case postMessage doesn't arrive (e.g. popup blocked from
    // scripting back, or user closed it manually right after connecting).
    pollDeadlineRef.current = Date.now() + POLL_TIMEOUT_MS;
    pollTimerRef.current = setInterval(async () => {
      if (popupRef.current && popupRef.current.closed) {
        // Popup was closed by the user (or by us) — do one last status
        // check in case they actually finished the flow.
        stopPolling();
        try {
          const data = await refreshStatus();
          setConnecting(false);
          if (data.connected) {
            addToast(data.google_email ? `Google Drive connected as ${data.google_email}.` : "Google Drive connected.", "success");
          }
        } catch {
          setConnecting(false);
        }
        return;
      }

      if (Date.now() > pollDeadlineRef.current) {
        stopPolling();
        setConnecting(false);
        return;
      }

      try {
        const data = await driveApi.status();
        if (data.connected) {
          finishConnectAttempt({ status: "connected", email: data.google_email });
        }
      } catch {
        // ignore transient errors while polling
      }
    }, POLL_INTERVAL_MS);
  }, [addToast, connecting, finishConnectAttempt, refreshStatus, stopPolling]);

  const disconnect = useCallback(async () => {
    setDisconnecting(true);
    try {
      await driveApi.disconnect();
      addToast("Google Drive disconnected.", "info");
      await refreshStatus();
    } catch (error) {
      addToast(error.message || "Unable to disconnect Google Drive.", "error");
    } finally {
      setDisconnecting(false);
    }
  }, [addToast, refreshStatus]);

  return { ...status, connecting, disconnecting, connect, disconnect, refreshStatus };
};
