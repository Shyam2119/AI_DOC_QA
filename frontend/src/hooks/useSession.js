import { useState, useCallback, useEffect, useRef } from "react";
import { sessionsApi, documentsApi, chatApi } from "../services/api";

// ── Sessions hook ──────────────────────────────────────────────────────────
export function useSessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await sessionsApi.list();
      setSessions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const createSession = useCallback(async (name = "New Session") => {
    const { data } = await sessionsApi.create(name);
    setSessions((prev) => [data, ...prev]);
    return data;
  }, []);

  const deleteSession = useCallback(async (id) => {
    await sessionsApi.delete(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const renameSession = useCallback(async (id, name) => {
    const { data } = await sessionsApi.update(id, { name });
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, ...data } : s)));
  }, []);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  return { sessions, loading, fetchSessions, createSession, deleteSession, renameSession };
}

// ── Active session hook ────────────────────────────────────────────────────
export function useSession(sessionId) {
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const pollRef = useRef(null);

  const fetchSession = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const { data } = await sessionsApi.get(sessionId);
      setSession(data);
      setMessages(data.messages || []);
      setDocuments(data.documents || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Poll documents that are still "processing"
  const pollDocuments = useCallback(async () => {
    if (!sessionId) return;
    try {
      const { data } = await documentsApi.listBySession(sessionId);
      setDocuments(data);
      const stillProcessing = data.some((d) => d.status === "processing");
      if (!stillProcessing && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch (e) {
      console.error(e);
    }
  }, [sessionId]);

  const startPolling = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = setInterval(pollDocuments, 2000);
  }, [pollDocuments]);

  const uploadDocument = useCallback(async (file, onProgress) => {
    const { data } = await documentsApi.upload(sessionId, file, onProgress);
    setDocuments((prev) => [data, ...prev]);
    startPolling();
    return data;
  }, [sessionId, startPolling]);

  const deleteDocument = useCallback(async (docId) => {
    await documentsApi.delete(docId);
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
  }, []);

  const sendMessage = useCallback(async (question) => {
    // Optimistic user bubble
    const tempUser = { id: `tmp-${Date.now()}`, role: "user", content: question, created_at: new Date().toISOString(), sources: [] };
    setMessages((prev) => [...prev, tempUser]);

    const { data } = await chatApi.ask(sessionId, question);
    setMessages((prev) => [
      ...prev.filter((m) => m.id !== tempUser.id),
      data.user_message,
      data.message,
    ]);
    return data.message;
  }, [sessionId]);

  const clearHistory = useCallback(async () => {
    await sessionsApi.clearMessages(sessionId);
    setMessages([]);
  }, [sessionId]);

  useEffect(() => {
    fetchSession();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchSession]);

  return {
    session, messages, documents, loading,
    uploadDocument, deleteDocument, sendMessage, clearHistory, fetchSession,
  };
}
