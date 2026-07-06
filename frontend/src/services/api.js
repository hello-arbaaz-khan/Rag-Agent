import axios from "axios";

const API_BASE_URL = "/api/";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000
});

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
  }
};

export default apiClient;
