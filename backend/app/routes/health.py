from flask import Blueprint, jsonify
from app import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    status = {
        "status": "ok",
        "database": "unknown",
        "embeddings": "not loaded",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "qa_model": "deepset/tinyroberta-squad2",
    }

    # Database check
    try:
        db.session.execute(db.text("SELECT 1"))
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # RAG service / embeddings check
    try:
        from app.services.rag_service import get_rag_service
        rag = get_rag_service()
        if rag.embeddings is not None:
            status["embeddings"] = "loaded"
        else:
            status["embeddings"] = "not loaded"
            status["status"] = "degraded"
    except Exception as e:
        status["embeddings"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return jsonify(status)
