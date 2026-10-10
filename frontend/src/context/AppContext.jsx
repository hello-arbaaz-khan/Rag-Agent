
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer
} from "react";
import { conversationApi, documentApi } from "../services/api.js";
import { useAuth } from "./AuthContext";

const AppContext = createContext(null);

const initialState = {
  documents: [],
  selectedDocumentId: null,
  conversations: [],
  activeConversation: null,
  messages: [],
  loadingDocuments: true,
  loadingConversations: false,
  loadingMessages: false,
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
        apiError: ""
      };

    case "RESET_DOCUMENTS":
      return { ...state, documents: [], loadingDocuments: true, apiError: "" };

    case "SET_API_ERROR":
      return { ...state, apiError: action.payload, loadingDocuments: false };

    case "SET_SELECTED_DOCUMENT":
      return { ...state, selectedDocumentId: action.payload };

    case "UPSERT_DOCUMENT": {
      const exists = state.documents.some((doc) => doc.id === action.payload.id);
      const documents = exists
        ? state.documents.map((doc) =>
            doc.id === action.payload.id ? { ...doc, ...action.payload } : doc
          )
        : [action.payload, ...state.documents];

      return {
        ...state,
        documents,
        selectedDocumentId: action.select
          ? action.payload.id
          : state.selectedDocumentId
      };
    }

    case "REMOVE_DOCUMENT":
      return {
        ...state,
        documents: state.documents.filter((doc) => doc.id !== action.payload)
      };

    case "SET_CONVERSATIONS":
      return { ...state, conversations: action.payload, loadingConversations: false };

    case "SET_CONVERSATIONS_LOADING":
      return { ...state, loadingConversations: action.payload };

    case "UPSERT_CONVERSATION": {
      const conversation = action.payload;
      const conversations = [
        conversation,
        ...state.conversations.filter((item) => item.id !== conversation.id)
      ].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

      return {
        ...state,
        conversations,
        activeConversation: conversation
      };
    }

    case "SET_ACTIVE_CONVERSATION":
      return { ...state, activeConversation: action.payload };

    case "SET_MESSAGES":
      return { ...state, messages: action.payload, loadingMessages: false };

    case "SET_MESSAGES_LOADING":
      return { ...state, loadingMessages: action.payload };

    case "APPEND_MESSAGES":
      return { ...state, messages: [...state.messages, ...action.payload] };

    case "ADD_TOAST":
      return { ...state, toasts: [...state.toasts, action.payload] };

    case "REMOVE_TOAST":
      return {
        ...state,
        toasts: state.toasts.filter((toast) => toast.id !== action.payload)
      };

    case "RESET_CHAT":
      return {
        ...state,
        activeConversation: null,
        messages: [],
        loadingMessages: false
      };

    case "REMOVE_CONVERSATION":
      return {
        ...state,
        conversations: state.conversations.filter(
          (item) => item.id !== action.payload
        ),
        activeConversation:
          state.activeConversation?.id === action.payload
            ? null
            : state.activeConversation,
        messages:
          state.activeConversation?.id === action.payload ? [] : state.messages
      };

    default:
      return state;
  }
};

export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { isAuthenticated } = useAuth();

  const addToast = useCallback((message, type = "info") => {
    const id = crypto.randomUUID();
    dispatch({ type: "ADD_TOAST", payload: { id, message, type } });
    window.setTimeout(
      () => dispatch({ type: "REMOVE_TOAST", payload: id }),
      3600
    );
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const response = await documentApi.listDocuments();
      const documents = response.data ?? response;
      dispatch({
        type: "SET_DOCUMENTS",
        payload: Array.isArray(documents) ? documents : []
      });
    } catch (error) {
      dispatch({ type: "SET_API_ERROR", payload: error.message });
    }
  }, []);

  const loadConversations = useCallback(async () => {
    dispatch({ type: "SET_CONVERSATIONS_LOADING", payload: true });
    try {
      const conversations = await conversationApi.list();
      dispatch({ type: "SET_CONVERSATIONS", payload: conversations });
    } catch (error) {
      addToast(error.message, "error");
      dispatch({ type: "SET_CONVERSATIONS_LOADING", payload: false });
    }
  }, [addToast]);

  const loadConversation = useCallback(async (conversationId) => {
    dispatch({ type: "SET_MESSAGES_LOADING", payload: true });
    try {
      const [conversation, messages] = await Promise.all([
        conversationApi.get(conversationId),
        conversationApi.listMessages(conversationId)
      ]);

      dispatch({ type: "SET_ACTIVE_CONVERSATION", payload: conversation });
      dispatch({ type: "SET_MESSAGES", payload: messages });
      dispatch({ type: "UPSERT_CONVERSATION", payload: conversation });
      return conversation;
    } catch (error) {
      dispatch({ type: "SET_MESSAGES", payload: [] });
      throw error;
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      dispatch({ type: "RESET_DOCUMENTS" });
      dispatch({ type: "RESET_CHAT" });
      dispatch({ type: "SET_CONVERSATIONS", payload: [] });
      return undefined;
    }

    dispatch({ type: "RESET_DOCUMENTS" });
    loadDocuments();
    loadConversations();

    const interval = window.setInterval(() => {
      loadDocuments();
    }, 10000);

    return () => window.clearInterval(interval);
  }, [isAuthenticated, loadDocuments, loadConversations]);

  const selectedDocument = useMemo(
    () =>
      state.documents.find((doc) => doc.id === state.selectedDocumentId) || null,
    [state.documents, state.selectedDocumentId]
  );

  const value = {
    ...state,
    selectedDocument,
    dispatch,
    addToast,
    loadDocuments,
    loadConversations,
    loadConversation
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