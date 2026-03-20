import React, { useState, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";
import RightPanel from "./components/RightPanel";
import { useSessions, useSession } from "./hooks/useSession";
import "./styles/global.css";
import "./App.css";

function EmptyState({ onCreate }) {
  return (
    <div className="empty-state">
      <div className="empty-state-content">
        <div className="empty-logo">
          <svg width="52" height="52" viewBox="0 0 52 52" fill="none">
            <rect width="52" height="52" rx="14" fill="var(--accent-dim)" stroke="var(--accent)" strokeWidth="1.5" />
            <path d="M16 36V18a2 2 0 012-2h12l6 6v14a2 2 0 01-2 2H18a2 2 0 01-2-2z" stroke="var(--accent)" strokeWidth="1.5" strokeLinejoin="round" fill="none"/>
            <path d="M30 16v6h6" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M21 26h10M21 30h7" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </div>
        <h1 className="empty-heading">DocMind</h1>
        <p className="empty-sub">
          Upload PDFs and ask questions — powered by LangChain RAG and GPT-4o-mini.
        </p>
        <button className="empty-cta" onClick={onCreate}>
          Start a new session
        </button>
        <div className="tech-badges">
          {["Flask", "LangChain", "OpenAI", "FAISS", "MySQL", "React"].map((t) => (
            <span key={t} className="tech-badge">{t}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function ActiveSession({ sessionId }) {
  const [sending, setSending] = useState(false);
  const {
    session, messages, documents, loading,
    uploadDocument, deleteDocument, sendMessage, clearHistory,
  } = useSession(sessionId);

  const hasDocuments = documents.some((d) => d.status === "ready");

  const handleSend = useCallback(async (question) => {
    setSending(true);
    try {
      await sendMessage(question);
    } finally {
      setSending(false);
    }
  }, [sendMessage]);

  return (
    <div className="session-layout">
      <ChatPanel
        messages={messages}
        onSend={handleSend}
        onClear={clearHistory}
        hasDocuments={hasDocuments}
        sending={sending}
      />
      <RightPanel
        session={session}
        documents={documents}
        onUpload={uploadDocument}
        onDelete={deleteDocument}
      />
    </div>
  );
}

export default function App() {
  const [activeId, setActiveId] = useState(null);
  const { sessions, loading, createSession, deleteSession, renameSession } = useSessions();

  const handleCreate = useCallback(async () => {
    const session = await createSession("New Session");
    setActiveId(session.id);
  }, [createSession]);

  const handleDelete = useCallback(async (id) => {
    await deleteSession(id);
    if (activeId === id) setActiveId(null);
  }, [deleteSession, activeId]);

  return (
    <div className="app-shell">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={setActiveId}
        onCreate={handleCreate}
        onDelete={handleDelete}
        onRename={renameSession}
        loading={loading}
      />

      <main className="app-main">
        {activeId ? (
          <ActiveSession key={activeId} sessionId={activeId} />
        ) : (
          <EmptyState onCreate={handleCreate} />
        )}
      </main>
    </div>
  );
}
