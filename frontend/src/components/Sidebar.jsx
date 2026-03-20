import React, { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { MessageSquare, Plus, Trash2, Edit3, Check, X, FileText, Bot } from "lucide-react";
import "./Sidebar.css";

export default function Sidebar({ sessions, activeId, onSelect, onCreate, onDelete, onRename, loading }) {
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  const startEdit = (e, session) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditValue(session.name);
  };

  const confirmEdit = async (e) => {
    e.stopPropagation();
    if (editValue.trim()) await onRename(editingId, editValue.trim());
    setEditingId(null);
  };

  const cancelEdit = (e) => {
    e.stopPropagation();
    setEditingId(null);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <Bot size={20} className="logo-icon" />
          <span className="logo-text">DocMind</span>
        </div>
        <button className="new-session-btn" onClick={onCreate} title="New session">
          <Plus size={16} />
          <span>New</span>
        </button>
      </div>

      <div className="sidebar-label">Sessions</div>

      <div className="session-list">
        {loading && sessions.length === 0 && (
          <div className="sessions-loading">
            {[1, 2, 3].map((i) => (
              <div key={i} className="session-skeleton skeleton" />
            ))}
          </div>
        )}

        {sessions.map((session) => (
          <div
            key={session.id}
            className={`session-item ${session.id === activeId ? "active" : ""}`}
            onClick={() => onSelect(session.id)}
          >
            <div className="session-icon">
              <MessageSquare size={14} />
            </div>

            <div className="session-body">
              {editingId === session.id ? (
                <input
                  className="session-rename-input"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") confirmEdit(e); if (e.key === "Escape") cancelEdit(e); }}
                  autoFocus
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="session-name truncate">{session.name}</span>
              )}
              <div className="session-meta">
                <span className="session-meta-item">
                  <FileText size={10} />
                  {session.document_count}
                </span>
                <span className="session-meta-item">
                  <MessageSquare size={10} />
                  {session.message_count}
                </span>
                <span className="session-time">
                  {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })}
                </span>
              </div>
            </div>

            <div className="session-actions">
              {editingId === session.id ? (
                <>
                  <button className="action-btn green" onClick={confirmEdit}><Check size={12} /></button>
                  <button className="action-btn" onClick={cancelEdit}><X size={12} /></button>
                </>
              ) : (
                <>
                  <button className="action-btn" onClick={(e) => startEdit(e, session)}><Edit3 size={12} /></button>
                  <button className="action-btn red" onClick={(e) => { e.stopPropagation(); onDelete(session.id); }}><Trash2 size={12} /></button>
                </>
              )}
            </div>
          </div>
        ))}

        {!loading && sessions.length === 0 && (
          <div className="sessions-empty">
            <MessageSquare size={32} className="empty-icon" />
            <p>No sessions yet</p>
            <p className="empty-sub">Click "New" to start</p>
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <span className="footer-text">AI Document Q&amp;A · RAG-powered</span>
      </div>
    </aside>
  );
}
