from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # Database Config
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        _db_user = os.getenv("DB_USER", "root")
        _db_pass = quote_plus(os.getenv("DB_PASSWORD", ""))   # URL-encode special chars
        _db_host = os.getenv("DB_HOST", "localhost")          # localhost works with Windows MySQL named pipe
        _db_port = os.getenv("DB_PORT", "3306")
        _db_name = os.getenv("DB_NAME", "ai_doc_qa")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}"
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 52428800))
    app.config["VECTOR_STORE_PATH"] = os.getenv("VECTOR_STORE_PATH", "vector_stores")

    # Ensure directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["VECTOR_STORE_PATH"], exist_ok=True)

    # Extensions
    db_ssl_env = os.getenv("DB_SSL", "false").lower() == "true"
    _db_host = os.getenv("DB_HOST", "localhost")
    
    # Auto-enable SSL for TiDB Cloud hosts
    if not db_ssl_env and ".tidbcloud.com" in _db_host:
        db_ssl_env = True

    if db_ssl_env:
        ca_path = os.getenv("DB_SSL_CA", "/etc/ssl/certs/ca-certificates.crt")
        # Fallback for common CA paths
        if not os.path.exists(ca_path):
            for fb in ["/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/ca-bundle.pem"]:
                if os.path.exists(fb):
                    ca_path = fb
                    break

        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {
                "ssl": {
                    "ca": ca_path
                }
            }
        }

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")], supports_credentials=True)

    # Blueprints
    from app.routes.documents import documents_bp
    from app.routes.sessions import sessions_bp
    from app.routes.chat import chat_bp
    from app.routes.health import health_bp

    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(health_bp, url_prefix="/api")

    return app
