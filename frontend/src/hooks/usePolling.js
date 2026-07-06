import { useEffect, useRef } from "react";
import { documentApi } from "../services/api";
import { useAppContext } from "../context/AppContext";

export const usePolling = () => {
  const { documents, dispatch, addToast } = useAppContext();
  const completedRef = useRef(new Set());

  useEffect(() => {
    const pendingDocuments = documents.filter((doc) => !Boolean(doc.is_processed) && !doc.processing_error);
    if (!pendingDocuments.length) return undefined;

    const poll = async () => {
      await Promise.all(
        pendingDocuments.map(async (doc) => {
          try {
            const status = await documentApi.getDocumentStatus(doc.id);
            dispatch({ type: "UPSERT_DOCUMENT", payload: { ...doc, ...status } });
            if (status.is_processed && !completedRef.current.has(doc.id)) {
              completedRef.current.add(doc.id);
              addToast(`${doc.name} finished processing.`, "success");
            }
          } catch (error) {
            dispatch({
              type: "UPSERT_DOCUMENT",
              payload: { ...doc, processing_error: error.message }
            });
          }
        })
      );
    };

    const intervalId = window.setInterval(poll, 3000);
    poll();
    return () => window.clearInterval(intervalId);
  }, [documents, dispatch, addToast]);
};
