import { useEffect, useRef, useMemo } from "react";
import { documentApi } from "../services/api";
import { useAppContext } from "../context/AppContext";

export const usePolling = () => {
  const { documents, dispatch, addToast } = useAppContext();
  const completedRef = useRef(new Set());
  const documentsRef = useRef(documents);

  // Keep documentsRef up to date with the latest state
  useEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  // Only track pending document IDs
  const pendingDocIds = useMemo(
    () => documents
      .filter((doc) => !Boolean(doc.is_processed) && !doc.processing_error)
      .map(doc => doc.id),
    [documents]
  );

  const pendingDocIdsRef = useRef(pendingDocIds);
  useEffect(() => {
    pendingDocIdsRef.current = pendingDocIds;
  }, [pendingDocIds]);

  useEffect(() => {
    if (pendingDocIds.length === 0) {
      return;
    }

    const poll = async () => {
      const currentPendingIds = pendingDocIdsRef.current;
      if (currentPendingIds.length === 0) return;

      await Promise.all(
        currentPendingIds.map(async (docId) => {
          try {
            const status = await documentApi.getDocumentStatus(docId);
            const currentDocs = documentsRef.current;
            const doc = currentDocs.find(d => d.id === docId);
            if (doc) {
              dispatch({ type: "UPSERT_DOCUMENT", payload: { ...doc, ...status } });
              if (status.is_processed && !completedRef.current.has(docId)) {
                completedRef.current.add(docId);
                addToast(`${doc.name} finished processing.`, "success");
              }
            }
          } catch (error) {
            const currentDocs = documentsRef.current;
            const doc = currentDocs.find(d => d.id === docId);
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

    // Run poll once immediately on mount or when pending list changes
    poll();

    // Poll every 5 seconds
    const intervalId = setInterval(poll, 5000);

    return () => {
      clearInterval(intervalId);
    };
  }, [pendingDocIds.join(",")]);
};

