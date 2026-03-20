import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Loader2, CheckCircle, XCircle, Trash2, AlertCircle } from "lucide-react";
import "./DropZone.css";

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function DocItem({ doc, onDelete }) {
  const statusIcon = {
    processing: <Loader2 size={14} className="spin doc-status-icon processing" />,
    ready: <CheckCircle size={14} className="doc-status-icon ready" />,
    error: <XCircle size={14} className="doc-status-icon error" />,
  };

  return (
    <div className={`doc-item fade-in ${doc.status}`}>
      <FileText size={16} className="doc-file-icon" />
      <div className="doc-info">
        <span className="doc-name truncate">{doc.filename}</span>
        <span className="doc-meta">
          {formatBytes(doc.file_size)}
          {doc.status === "ready" && ` · ${doc.page_count}p · ${doc.chunk_count} chunks`}
          {doc.status === "processing" && " · Processing…"}
          {doc.status === "error" && ` · Error: ${doc.error_message || "unknown"}`}
        </span>
      </div>
      {statusIcon[doc.status]}
      <button className="doc-delete-btn" onClick={() => onDelete(doc.id)} title="Remove document">
        <Trash2 size={12} />
      </button>
    </div>
  );
}

export default function DropZone({ documents, onUpload, onDelete }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (accepted, rejected) => {
    setError(null);
    if (rejected.length > 0) {
      setError("Only PDF files under 50MB are accepted.");
      return;
    }
    if (accepted.length === 0) return;

    setUploading(true);
    setProgress(0);
    try {
      for (const file of accepted) {
        await onUpload(file, setProgress);
      }
    } catch (e) {
      setError(e?.response?.data?.error || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxSize: 50 * 1024 * 1024,
    disabled: uploading,
    multiple: true,
  });

  const readyCount = documents.filter((d) => d.status === "ready").length;

  return (
    <div className="dropzone-wrapper">
      <div className="dropzone-header">
        <span className="dropzone-title">Documents</span>
        {readyCount > 0 && (
          <span className="ready-badge">{readyCount} ready</span>
        )}
      </div>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? "drag-active" : ""} ${uploading ? "uploading" : ""}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="drop-uploading">
            <Loader2 size={22} className="spin" style={{ color: "var(--accent)" }} />
            <span className="drop-text">Uploading… {progress}%</span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        ) : (
          <div className="drop-idle">
            <Upload size={22} className={`drop-icon ${isDragActive ? "active" : ""}`} />
            <span className="drop-text">
              {isDragActive ? "Drop PDFs here" : "Drop PDFs or click to browse"}
            </span>
            <span className="drop-sub">Max 50 MB per file</span>
          </div>
        )}
      </div>

      {error && (
        <div className="upload-error fade-in">
          <AlertCircle size={13} />
          {error}
        </div>
      )}

      {documents.length > 0 && (
        <div className="doc-list">
          {documents.map((doc) => (
            <DocItem key={doc.id} doc={doc} onDelete={onDelete} />
          ))}
        </div>
      )}

      {documents.length === 0 && !uploading && (
        <p className="doc-empty-hint">Upload a PDF to start asking questions.</p>
      )}
    </div>
  );
}
