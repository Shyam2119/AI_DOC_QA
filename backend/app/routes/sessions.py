from flask import Blueprint, request, jsonify
from app import db
from app.models import Session, Message

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/", methods=["GET"])
def list_sessions():
    sessions = Session.query.order_by(Session.updated_at.desc()).all()
    return jsonify([s.to_dict() for s in sessions])


@sessions_bp.route("/", methods=["POST"])
def create_session():
    data = request.get_json() or {}
    session = Session(name=data.get("name", "New Session"))
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201


@sessions_bp.route("/<session_id>", methods=["GET"])
def get_session(session_id):
    session = Session.query.get_or_404(session_id)
    result = session.to_dict()
    result["messages"] = [m.to_dict() for m in session.messages]
    result["documents"] = [d.to_dict() for d in session.documents]
    return jsonify(result)


@sessions_bp.route("/<session_id>", methods=["PATCH"])
def update_session(session_id):
    session = Session.query.get_or_404(session_id)
    data = request.get_json() or {}
    if "name" in data:
        session.name = data["name"]
    db.session.commit()
    return jsonify(session.to_dict())


@sessions_bp.route("/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    session = Session.query.get_or_404(session_id)
    db.session.delete(session)
    db.session.commit()
    return jsonify({"message": "Session deleted"})


@sessions_bp.route("/<session_id>/messages", methods=["GET"])
def get_messages(session_id):
    Session.query.get_or_404(session_id)
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    return jsonify([m.to_dict() for m in messages])


@sessions_bp.route("/<session_id>/clear", methods=["DELETE"])
def clear_messages(session_id):
    Session.query.get_or_404(session_id)
    Message.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    return jsonify({"message": "Chat history cleared"})
