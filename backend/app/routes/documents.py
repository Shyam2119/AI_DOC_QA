import os
import threading
import logging
import traceback
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app import db
from app.models import Document, Session
from app.services.rag_service import get_rag_service

documents_bp = Blueprint("documents", __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_document_async(app, doc_id, file_path, vector_store_path):
    """Background thread: parse PDF, embed, save FAISS index, update DB status."""
    print(f"[BG THREAD] Starting processing for doc_id={doc_id}", flush=True)
    with app.app_context():
        doc = Document.query.get(doc_id)
        if not doc:
            print(f"[BG THREAD] Doc {doc_id} not found in DB", flush=True)
            return
        try:
            print(f"[BG THREAD] Getting RAG service...", flush=True)
            rag = get_rag_service()
            print(f"[BG THREAD] Processing PDF: {file_path}", flush=True)
            page_count, chunk_count = rag.process_pdf(file_path, vector_store_path)
            doc.page_count = page_count
            doc.chunk_count = chunk_count
            doc.vector_store_path = vector_store_path
            doc.status = "ready"
            print(f"[BG THREAD] ✅ Done: {page_count} pages, {chunk_count} chunks", flush=True)
        except Exception as e:
            print(f"[BG THREAD] ❌ Error: {e}", flush=True)
            traceback.print_exc()
            doc.status = "error"
            doc.error_message = str(e)[:500]
        finally:
            db.session.commit()
            print(f"[BG THREAD] DB committed, status={doc.status}", flush=True)


@documents_bp.route("/upload/<session_id>", methods=["POST"])
def upload_document(session_id):
    session = Session.query.get_or_404(session_id)

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filename = secure_filename(file.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, f"{session_id}_{filename}")
    file.save(file_path)

    file_size = os.path.getsize(file_path)
    vector_store_path = os.path.join(
        current_app.config["VECTOR_STORE_PATH"],
        f"{session_id}_{filename.replace('.pdf', '')}"
    )

    doc = Document(
        session_id=session_id,
        filename=f"{session_id}_{filename}",
        original_filename=file.filename,
        file_size=file_size,
        status="processing",
    )
    db.session.add(doc)
    db.session.commit()

    print(f"[UPLOAD] Queued doc_id={doc.id} for background processing", flush=True)

    # Process in background thread
    app_obj = current_app._get_current_object()
    thread = threading.Thread(
        target=process_document_async,
        args=(app_obj, doc.id, file_path, vector_store_path),
        daemon=True,
    )
    thread.start()

    return jsonify(doc.to_dict()), 201


@documents_bp.route("/session/<session_id>", methods=["GET"])
def get_session_documents(session_id):
    Session.query.get_or_404(session_id)
    docs = Document.query.filter_by(session_id=session_id).order_by(Document.created_at.desc()).all()
    return jsonify([d.to_dict() for d in docs])


@documents_bp.route("/<doc_id>", methods=["GET"])
def get_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return jsonify(doc.to_dict())


@documents_bp.route("/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)

    # Clean up files
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    if doc.vector_store_path and os.path.exists(doc.vector_store_path):
        import shutil
        shutil.rmtree(doc.vector_store_path, ignore_errors=True)

    db.session.delete(doc)
    db.session.commit()
    return jsonify({"message": "Document deleted successfully"})
