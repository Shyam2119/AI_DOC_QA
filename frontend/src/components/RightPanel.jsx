import React from "react";
import DropZone from "./DropZone";
import { FileText, Layers, MessageSquare, Cpu } from "lucide-react";
import "./RightPanel.css";

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="stat-card">
      <Icon size={14} style={{ color }} />
      <div className="stat-body">
        <span className="stat-value">{value ?? "—"}</span>
        <span className="stat-label">{label}</span>
      </div>
    </div>
  );
}

export default function RightPanel({ session, documents, onUpload, onDelete }) {
  const readyDocs = documents.filter((d) => d.status === "ready");
  const totalPages = readyDocs.reduce((s, d) => s + (d.page_count || 0), 0);
  const totalChunks = readyDocs.reduce((s, d) => s + (d.chunk_count || 0), 0);

  return (
    <div className="right-panel">
      <div className="right-panel-header">
        <span className="right-panel-title">
          {session?.name || "Session"}
        </span>
      </div>

      <div className="right-panel-body">
        {/* Stats */}
        <div className="stats-grid">
          <StatCard icon={FileText} label="Documents" value={readyDocs.length} color="var(--accent)" />
          <StatCard icon={Layers} label="Pages" value={totalPages || null} color="var(--green)" />
          <StatCard icon={Cpu} label="Chunks" value={totalChunks || null} color="var(--amber)" />
          <StatCard icon={MessageSquare} label="Messages" value={session?.message_count} color="var(--text-secondary)" />
        </div>

        <div className="right-panel-divider" />

        {/* Upload zone */}
        <DropZone documents={documents} onUpload={onUpload} onDelete={onDelete} />

        <div className="right-panel-divider" />

        {/* Pipeline info */}
        <div className="pipeline-info">
          <p className="pipeline-title">RAG Pipeline</p>
          <div className="pipeline-steps">
            {["PDF ingestion (PyPDF)", "Chunk & embed (all-MiniLM-L6-v2)", "FAISS vector store", "LangChain retrieval (top-5)", "roberta-base-squad2 (extractive QA)"].map((step, i) => (
              <div key={i} className="pipeline-step">
                <span className="step-num">{i + 1}</span>
                <span className="step-label">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
