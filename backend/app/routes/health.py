from flask import Blueprint, jsonify
from app import db
import os

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    status = {"status": "ok", "database": "unknown", "openai": "configured"}
    try:
        db.session.execute(db.text("SELECT 1"))
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    if not os.getenv("OPENAI_API_KEY"):
        status["openai"] = "not configured"
        status["status"] = "degraded"

    return jsonify(status)
