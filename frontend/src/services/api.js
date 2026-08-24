import axios from "axios";
  import { authApi } from "./authApi";

const API_BASE_URL = "/api/";

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

const getErrorMessage = (error, fallback) => {
  const data = error?.response?.data;
  if (typeof data === "string") return data;
  if (data?.error) return data.error;
  if (data && typeof data === "object") {
    return Object.entries(data)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
      .join(" | ");
  }
  if (error?.message) return error.message;
  return fallback;
};

export const documentApi = {
  async listDocuments() {
    try {
      const { data } = await apiClient.get("list/");
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to load documents."));
    }
  },

  async uploadDocument(file, onUploadProgress) {
    const formData = new FormData();
    const extension = file.name.split(".").pop()?.toLowerCase() || "";
    formData.append("name", file.name.replace(/\.[^/.]+$/, "").slice(0, 25));
    formData.append("file_type", extension);
    formData.append("file", file);

    try {
      const { data } = await apiClient.post("upload/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress
      });
      return data.document || data;
    } catch (error) {
      if (error?.response?.data?.document) return error.response.data.document;
      throw new Error(getErrorMessage(error, "Document upload failed."));
    }
  },

  async getDocument(id) {
    try {
      const { data } = await apiClient.get(`detail/${id}/`);
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to load document details."));
    }
  },

  async getDocumentStatus(id) {
    try {
      const { data } = await apiClient.get(`status/${id}/`);
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to check processing status."));
    }
  },

  async deleteDocument(id) {
    try {
      await apiClient.delete(`detail/${id}/`);
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to delete document."));
    }
  },

  async askQuestion({ question, documentId }) {
    try {
      const { data } = await apiClient.post("question/", {
        question,
        document_id: documentId
      });
      return data.data ?? data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Answer generation failed."));
    }
  },

  async getChatHistory(documentId) {
    try {
      const { data } = await apiClient.get(`history/${documentId}/`);
      return data.data ?? data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to load chat history."));
    }
  },

  async clearChatHistory(documentId) {
    try {
      await apiClient.delete(`history/${documentId}/`);
    } catch (error) {
      throw new Error(getErrorMessage(error, "Unable to clear chat history."));
    }
  },

  async search(query) {
    try {
      const { data } = await apiClient.get("search/", {
        params: { query }
      });
      return data.data ?? data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Search failed."));
    }
  },

  async syncDrive() {
    try {
      const { data } = await apiClient.post("sync-drive/");
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Drive sync failed."));
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
            // Attempt to refresh the access token
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