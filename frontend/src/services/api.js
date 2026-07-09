import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Sessions
export const sessionsApi = {
  list: () => api.get("/sessions/"),
  create: (name) => api.post("/sessions/", { name }),
  get: (id) => api.get(`/sessions/${id}`),
  update: (id, data) => api.patch(`/sessions/${id}`, data),
  delete: (id) => api.delete(`/sessions/${id}`),
  getMessages: (id) => api.get(`/sessions/${id}/messages`),
  clearMessages: (id) => api.delete(`/sessions/${id}/clear`),
};

// Documents
export const documentsApi = {
  upload: (sessionId, file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    return api.post(`/documents/upload/${sessionId}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
  },
  listBySession: (sessionId) => api.get(`/documents/session/${sessionId}`),
  get: (id) => api.get(`/documents/${id}`),
  delete: (id) => api.delete(`/documents/${id}`),
};

// Chat
export const chatApi = {
  ask: (sessionId, question) => api.post(`/chat/ask/${sessionId}`, { question }),
};

// Health
export const healthApi = {
  check: () => api.get("/health"),
};

export default api;
