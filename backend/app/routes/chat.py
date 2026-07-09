import logging
from flask import Blueprint, request, jsonify
from app import db
from app.models import Session, Message, Document
from app.services.rag_service import get_rag_service

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)


def build_chat_history(messages, limit=10):
    """Convert DB messages to LangChain chat history format."""
    history = []
    recent = [m for m in messages if m.role in ("user", "assistant")][-limit:]
    i = 0
    while i < len(recent) - 1:
        if recent[i].role == "user" and recent[i + 1].role == "assistant":
            history.append((recent[i].content, recent[i + 1].content))
            i += 2
        else:
            i += 1
    return history


@chat_bp.route("/ask/<session_id>", methods=["POST"])
def ask(session_id):
    session = Session.query.get_or_404(session_id)
    data = request.get_json()

    if not data or not data.get("question", "").strip():
        return jsonify({"error": "Question is required"}), 400

    question = data["question"].strip()

    # Get ready documents for this session
    docs = Document.query.filter_by(session_id=session_id, status="ready").all()
    vector_store_paths = [d.vector_store_path for d in docs if d.vector_store_path]

    # Save user message
    user_msg = Message(session_id=session_id, role="user", content=question)
    db.session.add(user_msg)
    db.session.commit()

    # Build chat history from previous messages
    all_messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    chat_history = build_chat_history(all_messages[:-1])  # exclude the message we just added

    try:
        rag = get_rag_service()
        result = rag.query(question, vector_store_paths, chat_history)

        # Save assistant message
        assistant_msg = Message(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            sources=result["sources"],
            tokens_used=result["tokens_used"],
        )
        db.session.add(assistant_msg)

        # Update session timestamp
        from datetime import datetime
        session.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": assistant_msg.to_dict(),
            "user_message": user_msg.to_dict(),
        })

    except Exception as e:
        logger.error(f"RAG query error: {e}")
        error_msg = Message(
            session_id=session_id,
            role="assistant",
            content=f"Sorry, an error occurred while processing your question: {str(e)}",
            sources=[],
        )
        db.session.add(error_msg)
        db.session.commit()
        return jsonify({"error": str(e), "message": error_msg.to_dict()}), 500
