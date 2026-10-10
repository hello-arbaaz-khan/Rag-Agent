import axios from "axios";
import { authApi } from "./authApi";

// FastAPI service (documents, chat, search, Google Drive).
// Authentication remains on Django at /api/auth/.
const API_BASE_URL = "/api/v1/";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

// Attach the access token to requests.
apiClient.interceptors.request.use(
  (config) => {
    const tokensJson = localStorage.getItem("documind_auth_tokens");

    if (tokensJson) {
      try {
        const tokens = JSON.parse(tokensJson);

        if (tokens?.access) {
          config.headers.Authorization = `Bearer ${tokens.access}`;
        }
      } catch (error) {
        console.error("Failed to parse auth tokens:", error);
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Normalize API errors.
const getErrorMessage = (error, fallback) => {
  const data = error?.response?.data;

  if (typeof data === "string" && data) {
    return data;
  }

  const detail = data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return (
      detail
        .map((item) => {
          const field = Array.isArray(item?.loc)
            ? item.loc
                .filter((part) => part !== "body" && part !== "query")
                .join(".")
            : "";

          return field ? `${field}: ${item?.msg}` : item?.msg;
        })
        .filter(Boolean)
        .join(" | ") || fallback
    );
  }

  if (detail && typeof detail === "object") {
    return detail.message || detail.processing_error || fallback;
  }

  return data?.error || data?.message || error?.message || fallback;
};

// Normalize conversation endpoint errors.
const getConversationErrorMessage = (error, fallback) =>
  getErrorMessage(error, fallback);

// Search results from FastAPI.
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
  matched_snippet: result.matched_snippet ?? undefined,
});

// --------------------------------------------------
// DOCUMENT API
// --------------------------------------------------

export const documentApi = {
  async listDocuments() {
    try {
      const { data } = await apiClient.get("documents");
      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Unable to load documents.")
      );
    }
  },

  async uploadDocument(file, onUploadProgress) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const { data } = await apiClient.post("documents", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress,
      });

      return data;
    } catch (error) {
      // If the backend identifies a previously uploaded file, reuse it.
      const existingId = error?.response?.data?.detail?.document_id;

      if (error?.response?.status === 409 && existingId) {
        return this.getDocument(existingId);
      }

      throw new Error(
        getErrorMessage(error, "Document upload failed.")
      );
    }
  },

  async getDocument(id) {
    try {
      const { data } = await apiClient.get(`documents/${id}`);
      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Unable to load document details.")
      );
    }
  },

  async getDocumentStatus(id) {
    try {
      const { data } = await apiClient.get(`documents/${id}`);
      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Unable to check processing status.")
      );
    }
  },

  async deleteDocument(id) {
    try {
      await apiClient.delete(`documents/${id}`);
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Unable to delete document.")
      );
    }
  },

  async askQuestion({ question, documentId }) {
    try {
      const { data } = await apiClient.post("chat", {
        question,
        document_id: documentId,
      });

      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Answer generation failed.")
      );
    }
  },

  async getChatHistory(documentId) {
    try {
      const { data } = await apiClient.get(
        `chat/history/${documentId}`
      );

      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Unable to load chat history.")
      );
    }
  },

  async clearChatHistory(documentId) {
    try {
      await apiClient.delete(`chat/history/${documentId}`);
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Unable to clear chat history.")
      );
    }
  },

  async search(query) {
    try {
      const params = { limit: 100 };

      if (query && query.trim()) {
        params.query = query.trim();
      }

      const { data } = await apiClient.get("search", { params });

      return {
        ...data,
        results: (data.results || []).map(toSearchRow),
      };
    } catch (error) {
      throw new Error(getErrorMessage(error, "Search failed."));
    }
  },

  async syncDrive() {
    try {
      const { data } = await apiClient.post("drive/sync");
      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(error, "Drive sync failed.")
      );
    }
  },
};

// --------------------------------------------------
// CONVERSATION API
// --------------------------------------------------

export const conversationApi = {
  async list() {
    try {
      const { data } = await apiClient.get("chat/conversations");

      return Array.isArray(data)
        ? data
        : data?.results || [];
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to load conversations."
        )
      );
    }
  },

  async get(conversationId) {
    try {
      const { data } = await apiClient.get(
        `chat/conversations/${conversationId}`
      );

      return data;
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to load this conversation."
        )
      );
    }
  },

  async create({ title, documentIds = [] }) {
    try {
      const { data } = await apiClient.post(
        "chat/conversations",
        {
          title,
          document_ids: documentIds,
        }
      );

      return data;
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to create conversation."
        )
      );
    }
  },

  async listMessages(conversationId) {
    try {
      const { data } = await apiClient.get(
        `chat/conversations/${conversationId}/messages`
      );

      return Array.isArray(data)
        ? data
        : data?.results || [];
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to load messages."
        )
      );
    }
  },

  async sendMessage(conversationId, question) {
    try {
      const { data } = await apiClient.post(
        `chat/conversations/${conversationId}/messages`,
        { question }
      );

      return data;
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to generate an answer."
        )
      );
    }
  },

  async attachDocuments(conversationId, documentIds) {
    try {
      const { data } = await apiClient.post(
        `chat/conversations/${conversationId}/documents`,
        {
          document_ids: documentIds,
        }
      );

      return data;
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to attach documents."
        )
      );
    }
  },

  async uploadDocuments(conversationId, files) {
    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const { data } = await apiClient.post(
        `chat/conversations/${conversationId}/documents/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      return data;
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to upload documents to this conversation."
        )
      );
    }
  },

  async delete(conversationId) {
    try {
      await apiClient.delete(
        `chat/conversations/${conversationId}`
      );
    } catch (error) {
      throw new Error(
        getConversationErrorMessage(
          error,
          "Unable to delete conversation."
        )
      );
    }
  },
};

// --------------------------------------------------
// GOOGLE DRIVE API
// --------------------------------------------------

export const driveApi = {
  async connect() {
    try {
      const { data } = await apiClient.get("drive/connect");
      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(
          error,
          "Unable to start Google Drive connection."
        )
      );
    }
  },

  async status() {
    try {
      const { data } = await apiClient.get("drive/status");
      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(
          error,
          "Unable to check Google Drive status."
        )
      );
    }
  },

  async disconnect() {
    try {
      const { data } = await apiClient.delete(
        "drive/disconnect"
      );

      return data;
    } catch (error) {
      throw new Error(
        getErrorMessage(
          error,
          "Unable to disconnect Google Drive."
        )
      );
    }
  },
};

// --------------------------------------------------
// ACCESS TOKEN REFRESH
// --------------------------------------------------

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      try {
        const tokensJson = localStorage.getItem(
          "documind_auth_tokens"
        );

        if (tokensJson) {
          const tokens = JSON.parse(tokensJson);

          if (tokens?.refresh) {
            const data = await authApi.refreshAccessToken(
              tokens.refresh
            );

            const newTokens = {
              ...tokens,
              access: data.access,
            };

            if (data.refresh) {
              newTokens.refresh = data.refresh;
            }

            localStorage.setItem(
              "documind_auth_tokens",
              JSON.stringify(newTokens)
            );

            originalRequest.headers =
              originalRequest.headers || {};

            originalRequest.headers.Authorization =
              `Bearer ${data.access}`;

            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        localStorage.removeItem("documind_auth_tokens");
        localStorage.removeItem("documind_auth_user");

        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
