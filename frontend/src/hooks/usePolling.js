import { useEffect, useRef, useMemo } from "react";
import { documentApi } from "../services/api";
import { useAppContext } from "../context/AppContext";

export const usePolling = () => {
  const { documents, dispatch, addToast } = useAppContext();
  const completedRef = useRef(new Set());
  const intervalRef = useRef(null);

  // Only track pending document IDs (not the full objects)
  const pendingDocIds = useMemo(
    () => documents
      .filter((doc) => !Boolean(doc.is_processed) && !doc.processing_error)
      .map(doc => doc.id),
    [documents]
  );

  useEffect(() => {
    if (pendingDocIds.length === 0) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const poll = async () => {
      await Promise.all(
        pendingDocIds.map(async (docId) => {
          try {
            const status = await documentApi.getDocumentStatus(docId);
            const doc = documents.find(d => d.id === docId);
            if (doc) {
              dispatch({ type: "UPSERT_DOCUMENT", payload: { ...doc, ...status } });
              if (status.is_processed && !completedRef.current.has(docId)) {
                completedRef.current.add(docId);
                addToast(`${doc.name} finished processing.`, "success");
              }
            }
          } catch (error) {
            const doc = documents.find(d => d.id === docId);
            if (doc) {
              dispatch({
                type: "UPSERT_DOCUMENT",
                payload: { ...doc, processing_error: error.message }
              });
            }
          }
        })
      );
    };

    // Poll every 5 seconds
    if (!intervalRef.current) {
      poll();
      intervalRef.current = window.setInterval(poll, 5000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [pendingDocIds, documents, dispatch, addToast]);
};
