import { useEffect, useRef } from "react";
import { documentApi } from "../services/api";
import { useAppContext } from "../context/AppContext";

const SYNC_INTERVAL_MS = 60 * 1000; // 1 minute

/**
 * Automatically calls /api/sync-drive/ every 1 minute for the lifetime
 * of the app (mounted once at the App root), so Drive changes are picked
 * up without any manual "Sync Drive" button.
 */
export const useDriveAutoSync = () => {
  const { addToast } = useAppContext();
  const syncingRef = useRef(false);

  useEffect(() => {
    const runSync = async () => {
      // Avoid overlapping calls if a previous sync is still in flight
      if (syncingRef.current) return;
      syncingRef.current = true;
      try {
        await documentApi.syncDrive();
      } catch (error) {
        addToast(error.message || "Drive auto-sync failed.", "error");
      } finally {
        syncingRef.current = false;
      }
    };

    // Run once immediately, then every 1 minute
    runSync();
    const intervalId = setInterval(runSync, SYNC_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, []);
};