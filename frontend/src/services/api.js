import axios from "axios";
import { authApi } from "./authApi";

// FastAPI service (documents, chat, search, Google Drive).
// In dev this is proxied by Vite (see vite.config.js); authentication stays
// on Django at /api/auth/ (see authApi.js).
const API_BASE_URL = "/api/v1/";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000
});

// Add auth token to all requests
apiClient.interceptors.request.use((config) => {
  const tokensJson = localStorage.getItem("documind_auth_tokens");
  if (tokensJson) {
    try {
      const tokens = JSON.parse(tokensJson);
      if (tokens?.access) {
        config.headers.Authorization = `Bearer ${tokens.access}`;
      }
    } catch (e) {
      console.error("Failed to parse auth tokens:", e);
    }
  }
  return config;
}, (error) => Promise.reject(error));

// FastAPI errors look like { detail: "text" }, { detail: { message, ... } }
// or, for validation failures, { detail: [{ loc, msg, type }, ...] }.
const getErrorMessage = (error, fallback) => {
  const data = error?.response?.data;
  if (typeof data === "string" && data) return data;

  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item?.loc) ? item.loc.filter((p) => p !== "body" && p !== "query").join(".") : "";
        return field ? `${field}: ${item?.msg}` : item?.msg;
      })
      .filter(Boolean)
      .join(" | ");
  }
  if (detail && typeof detail === "object") {
    return detail.message || detail.processing_error || fallback;
  }

  if (data?.error) return data.error;
  if (data?.message) return data.message;
  if (error?.message) return error.message;
  return fallback;
};

// Search results from FastAPI are document records; the Advanced Search UI
// was built around Drive-sync rows, so map one onto the other.
const toSearchRow = (result) => ({
  drive_file_id: String(result.id),
  name: result.name,
  mime_type: result.file_type,
  drive_modified_at: result.uploaded_at,
  sync_status: result.is_processed ? "indexed" : "processing",
  document_id: result.id,
  total_chunks: undefined,
  file_size: result.file_size,
  relevance_score: result.relevance_score ?? undefined,
  matched_snippet: result.matched_snippet ?? undefined
});

export const documentApi = {
  async listDocuments() {
    try {
      const { data } = await apiClient.get("documents");
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to load documents."));
    }
  },

  async uploadDocument(file, onUploadProgress) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const { data } = await apiClient.post("documents", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress
      });
      return data;
    } catch (error) {
      // Same file uploaded before: FastAPI answers 409 with the existing id.
      const existingId = error?.response?.data?.detail?.document_id;
      if (error?.response?.status === 409 && existingId) {
        return this.getDocument(existingId);
      }
      throw new Error(getErrorMessage(error, "Document upload failed."));
    }
  },

  async getDocument(id) {
    try {
      const { data } = await apiClient.get(`documents/${id}`);
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to load document details."));
    }
  },

  // FastAPI has no separate /status route: the document record itself
  // carries is_processed / processing_error.
  async getDocumentStatus(id) {
    try {
      const { data } = await apiClient.get(`documents/${id}`);
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to check processing status."));
    }
  },

  async deleteDocument(id) {
    try {
      await apiClient.delete(`documents/${id}`);
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to delete document."));
    }
  },

  async askQuestion({ question, documentId }) {
    try {
      const { data } = await apiClient.post("chat", {
        question,
        document_id: documentId
      });
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Answer generation failed."));
    }
  },

  async getChatHistory(documentId) {
    try {
      const { data } = await apiClient.get(`chat/history/${documentId}`);
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to load chat history."));
    }
  },

  async clearChatHistory(documentId) {
    try {
      await apiClient.delete(`chat/history/${documentId}`);
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to clear chat history."));
    }
  },

  async search(query) {
    try {
      // FastAPI rejects an empty `query`; omit it to list everything.
      const params = { limit: 100 };
      if (query && query.trim()) params.query = query.trim();
      const { data } = await apiClient.get("search", { params });
      return { ...data, results: (data.results || []).map(toSearchRow) };
    } catch (error) {
      throw new Error(getErrorMessage(error, "Search failed."));
    }
  },

  async syncDrive() {
    try {
      const { data } = await apiClient.post("drive/sync");
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Drive sync failed."));
    }
  },
};

export const driveApi = {
  /** Returns { auth_url } — open this in a popup to start the Google OAuth flow. */
  async connect() {
    try {
      const { data } = await apiClient.get("drive/connect");
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to start Google Drive connection."));
    }
  },

  /** Returns { connected, google_email?, connected_at? }. */
  async status() {
    try {
      const { data } = await apiClient.get("drive/status");
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to check Google Drive status."));
    }
  },

  async disconnect() {
    try {
      const { data } = await apiClient.delete("drive/disconnect");
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to disconnect Google Drive."));
    }
  },
};

// Response interceptor to handle expired access tokens
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if error is 401 (Unauthorized) and has not been retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const tokensJson = localStorage.getItem("documind_auth_tokens");
        if (tokensJson) {
          const tokens = JSON.parse(tokensJson);
          if (tokens?.refresh) {
            // Attempt to refresh the access token (Django: /api/auth/token/refresh/)
            const data = await authApi.refreshAccessToken(tokens.refresh);

            // Save new tokens
            const newTokens = { ...tokens, access: data.access };
            if (data.refresh) {
              newTokens.refresh = data.refresh;
            }
            localStorage.setItem("documind_auth_tokens", JSON.stringify(newTokens));

            // Retry the original request
            originalRequest.headers.Authorization = `Bearer ${data.access}`;
            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        // If refresh fails, clear auth state and redirect to login
        localStorage.removeItem("documind_auth_tokens");
        localStorage.removeItem("documind_auth_user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;