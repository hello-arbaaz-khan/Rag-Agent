import { createContext, useCallback, useContext, useEffect, useMemo, useReducer } from "react";
import { documentApi } from "../services/api";

const AppContext = createContext(null);

const CHAT_STORAGE_KEY = "documind_chat_history";

const loadChatHistoryFromStorage = () => {
  try {
    const stored = localStorage.getItem(CHAT_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
};

const saveChatHistoryToStorage = (chatHistory) => {
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(chatHistory));
  } catch (err) {
    console.warn("Failed to save chat history to localStorage:", err);
  }
};

const initialState = {
  documents: [],
  selectedDocumentId: null,
  chatHistory: loadChatHistoryFromStorage(),
  loadingDocuments: true,
  apiError: "",
  toasts: []
};

const reducer = (state, action) => {
  switch (action.type) {
    case "SET_DOCUMENTS":
      return {
        ...state,
        documents: action.payload,
        loadingDocuments: false,
        apiError: "",
        selectedDocumentId:
          state.selectedDocumentId || action.payload[0]?.id || null
      };
    case "SET_API_ERROR":
      return { ...state, apiError: action.payload, loadingDocuments: false };
    case "SET_SELECTED_DOCUMENT":
      return { ...state, selectedDocumentId: action.payload };
    case "UPSERT_DOCUMENT": {
      const exists = state.documents.some((doc) => doc.id === action.payload.id);
      const documents = exists
        ? state.documents.map((doc) => (doc.id === action.payload.id ? { ...doc, ...action.payload } : doc))
        : [action.payload, ...state.documents];
      return {
        ...state,
        documents,
        selectedDocumentId: action.select ? action.payload.id : state.selectedDocumentId
      };
    }
    case "REMOVE_DOCUMENT": {
      const documents = state.documents.filter((doc) => doc.id !== action.payload);
      const chatHistory = { ...state.chatHistory };
      delete chatHistory[action.payload];
      saveChatHistoryToStorage(chatHistory);
      return {
        ...state,
        documents,
        chatHistory,
        selectedDocumentId:
          state.selectedDocumentId === action.payload ? documents[0]?.id || null : state.selectedDocumentId
      };
    }
    case "ADD_MESSAGE": {
      const current = state.chatHistory[action.documentId] || [];
      const updated = {
        ...state.chatHistory,
        [action.documentId]: [...current, action.payload]
      };
      saveChatHistoryToStorage(updated);
      return {
        ...state,
        chatHistory: updated
      };
    }
    case "CLEAR_CHAT": {
      const updated = {
        ...state.chatHistory,
        [action.documentId]: []
      };
      saveChatHistoryToStorage(updated);
      return {
        ...state,
        chatHistory: updated
      };
    }
    case "SET_CHAT_HISTORY": {
      const updated = action.payload;
      saveChatHistoryToStorage(updated);
      return {
        ...state,
        chatHistory: updated
      };
    }
    case "ADD_TOAST":
      return {
        ...state,
        toasts: [...state.toasts, action.payload]
      };
    case "REMOVE_TOAST":
      return {
        ...state,
        toasts: state.toasts.filter((toast) => toast.id !== action.payload)
      };
    default:
      return state;
  }
};

export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const addToast = useCallback((message, type = "info") => {
    const id = crypto.randomUUID();
    dispatch({ type: "ADD_TOAST", payload: { id, message, type } });
    window.setTimeout(() => dispatch({ type: "REMOVE_TOAST", payload: id }), 3600);
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const response = await documentApi.listDocuments();
      const documents = response.data ?? response;
      dispatch({ type: "SET_DOCUMENTS", payload: Array.isArray(documents) ? documents : [] });
    } catch (error) {
      dispatch({ type: "SET_API_ERROR", payload: error.message });
    }
  }, []);

useEffect(() => {
  loadDocuments();

  // Only poll for list updates if no documents are processing
  // (usePolling.js handles status updates for processing docs)
  const interval = setInterval(() => {
    loadDocuments();
  }, 10000);

  return () => clearInterval(interval);
}, [loadDocuments]);

  const selectedDocument = useMemo(
    () => state.documents.find((doc) => doc.id === state.selectedDocumentId) || null,
    [state.documents, state.selectedDocumentId]
  );

  const value = {
    ...state,
    selectedDocument,
    dispatch,
    addToast,
    loadDocuments
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used inside AppProvider");
  }
  return context;
};
