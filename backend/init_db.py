"""
Run this script once to create the MySQL database and all tables.
Usage: python init_db.py

This script:
1. Reads DB credentials from .env
2. Creates the database if it doesn't exist
3. Creates all tables using SQLAlchemy models
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "ai_doc_qa")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Step 1: Create the database if it doesn't exist
print(f"Connecting to MySQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")
try:
    import pymysql
    db_ssl_env = os.getenv("DB_SSL", "false").lower() == "true"
    
    # Auto-enable SSL for TiDB Cloud hosts
    if not db_ssl_env and ".tidbcloud.com" in DB_HOST:
        print(f"  [AUTO] Detected TiDB Cloud host ({DB_HOST}). Enabling SSL...")
        db_ssl_env = True

    ssl_config = None
    if db_ssl_env:
        ca_path = os.getenv("DB_SSL_CA", "/etc/ssl/certs/ca-certificates.crt")
        # Fallback for common CA paths if the default doesn't exist
        if not os.path.exists(ca_path):
            fallbacks = ["/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/ca-bundle.pem"]
            for fb in fallbacks:
                if os.path.exists(fb):
                    ca_path = fb
                    break
        
        ssl_config = {"ca": ca_path}
        print(f"  [SSL] Using CA cert: {ca_path}")

    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
        ssl=ssl_config,
    )
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Database '{DB_NAME}' is ready.")
except Exception as e:
    print(f"❌ Could not connect to MySQL: {e}")
    print("\nPlease check your environment variables:")
    print(f"  DB_HOST={DB_HOST}")
    print(f"  DB_PORT={DB_PORT}")
    print(f"  DB_USER={DB_USER}")
    print(f"  DB_PASSWORD={'*' * len(DB_PASSWORD) if DB_PASSWORD else '(empty)'}")
    print(f"  DB_SSL={os.getenv('DB_SSL', 'false')}")
    sys.exit(1)

# Step 2: Create all tables via SQLAlchemy
from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ All database tables created successfully.")
    print("\nYou can now start the server with: python run.py")
