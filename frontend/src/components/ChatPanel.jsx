import React, { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send, Loader2, Trash2, BookOpen, ChevronDown, ChevronUp,
  User, Bot, Copy, Check, Download, Lightbulb
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import "./ChatPanel.css";

// ── Suggestion chips by document type ───────────────────────────────────────
const SUGGESTIONS = [
  "Summarize the main points",
  "What are the key requirements?",
  "List all technologies mentioned",
  "What are the important dates?",
  "What is the candidate's name?",
  "What contact details are available?",
];

// ── Copy button ──────────────────────────────────────────────────────────────
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handle = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button className="copy-btn" onClick={handle} title="Copy answer">
      {copied ? <Check size={12} /> : <Copy size={12} />}
    </button>
  );
}

// ── Source card ──────────────────────────────────────────────────────────────
function SourceCard({ source }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="source-card">
      <button className="source-header" onClick={() => setOpen(p => !p)}>
        <BookOpen size={11} />
        <span className="source-file">{source.file}</span>
        <span className="source-page">p.{source.page}</span>
        {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
      </button>
      {open && <p className="source-snippet">{source.snippet}</p>}
    </div>
  );
}

// ── Message bubble ───────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  const [showSources, setShowSources] = useState(false);
  const hasSources = !isUser && msg.sources && msg.sources.length > 0;

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"} fade-in`}>
      <div className="message-avatar">
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>
      <div className="message-content-wrap">
        <div className={`message-bubble ${isUser ? "bubble-user" : "bubble-assistant"}`}>
          {isUser ? (
            <p className="message-text">{msg.content}</p>
          ) : (
            <div className="md-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
            </div>
          )}
        </div>

        <div className="message-footer">
          <span className="message-time">
            {msg.created_at
              ? formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })
              : "just now"}
          </span>
          {!isUser && <CopyButton text={msg.content} />}
          {hasSources && (
            <button className="sources-toggle" onClick={() => setShowSources(p => !p)}>
              <BookOpen size={11} />
              {msg.sources.length} source{msg.sources.length > 1 ? "s" : ""}
              {showSources ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
            </button>
          )}
        </div>

        {showSources && hasSources && (
          <div className="sources-list fade-in">
            {msg.sources.map((s, i) => <SourceCard key={i} source={s} />)}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Typing indicator ─────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="message-row assistant-row fade-in">
      <div className="message-avatar"><Bot size={14} /></div>
      <div className="typing-indicator"><span /><span /><span /></div>
    </div>
  );
}

// ── Export chat ──────────────────────────────────────────────────────────────
function exportChat(messages) {
  const lines = messages.map(m =>
    `[${m.role.toUpperCase()}] ${m.content}\n`
  ).join("\n");
  const blob = new Blob([lines], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `chat-export-${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Main component ───────────────────────────────────────────────────────────
const MAX_CHARS = 500;

export default function ChatPanel({ messages, onSend, onClear, hasDocuments, sending }) {
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const charsLeft = MAX_CHARS - input.length;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const handleSubmit = useCallback(async (e) => {
    e?.preventDefault();
    const q = input.trim();
    if (!q || sending) return;
    setInput("");
    setShowSuggestions(false);
    await onSend(q);
    inputRef.current?.focus();
  }, [input, sending, onSend]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
    if (e.key === "Escape") setShowSuggestions(false);
  };

  const pickSuggestion = (q) => {
    setInput(q);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  return (
    <div className="chat-panel">
      {/* Toolbar */}
      <div className="chat-toolbar">
        <span className="chat-toolbar-title">Chat</span>
        <div className="chat-toolbar-actions">
          {messages.length > 0 && (
            <button className="toolbar-btn" onClick={() => exportChat(messages)} title="Export chat">
              <Download size={13} /> Export
            </button>
          )}
          {messages.length > 0 && (
            <button className="toolbar-btn clear-btn" onClick={onClear} title="Clear history">
              <Trash2 size={13} /> Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="messages-area">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon"><Bot size={36} /></div>
            <h3 className="chat-empty-title">Ask anything about your documents</h3>
            <p className="chat-empty-sub">
              {hasDocuments
                ? "Your documents are ready. Try a suggestion or ask your own question."
                : "Upload a PDF document first, then ask questions here."}
            </p>
            {hasDocuments && (
              <div className="suggestion-chips">
                {SUGGESTIONS.map(q => (
                  <button key={q} className="suggestion-chip" onClick={() => pickSuggestion(q)}>
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
        {sending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <form className="chat-input-area" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          {hasDocuments && (
            <button
              type="button"
              className={`suggest-btn ${showSuggestions ? "active" : ""}`}
              onClick={() => setShowSuggestions(p => !p)}
              title="Show suggestions"
            >
              <Lightbulb size={15} />
            </button>
          )}
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value.slice(0, MAX_CHARS))}
            onKeyDown={handleKeyDown}
            placeholder={hasDocuments ? "Ask a question… (Enter to send, Shift+Enter for newline)" : "Upload a document to start chatting…"}
            disabled={sending || !hasDocuments}
            rows={1}
          />
          {input.length > 0 && (
            <span className={`char-counter ${charsLeft < 50 ? "warn" : ""}`}>
              {charsLeft}
            </span>
          )}
          <button
            type="submit"
            className={`send-btn ${input.trim() && !sending ? "active" : ""}`}
            disabled={!input.trim() || sending || !hasDocuments}
          >
            {sending ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
          </button>
        </div>

        {/* Inline suggestion dropdown */}
        {showSuggestions && (
          <div className="suggestions-dropdown fade-in">
            {SUGGESTIONS.map(q => (
              <button key={q} type="button" className="suggestion-item" onClick={() => pickSuggestion(q)}>
                <Lightbulb size={12} /> {q}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  );
}
