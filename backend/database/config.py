import sqlite3
import os

DB_NAME = "ledgerlens.db"
UPLOADS_DIR = "uploads"

def init_db():
    """Initializes the database and runs necessary schema migrations."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Create the base table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            status TEXT NOT NULL,
            extracted_json TEXT,
            reviewed_json TEXT,
            overall_confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            perceptual_hash TEXT
        )
    ''')
    
    # 2. Migration: Check existing columns using PRAGMA
    cursor.execute("PRAGMA table_info(documents)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # 3. Add updated_at if missing
    if 'updated_at' not in columns:
        cursor.execute("ALTER TABLE documents ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    # 4. Add perceptual_hash if missing
    if 'perceptual_hash' not in columns:
        print("Migration: Adding 'perceptual_hash' column to 'documents' table...")
        cursor.execute("ALTER TABLE documents ADD COLUMN perceptual_hash TEXT")
        
    conn.commit()
    conn.close()

def get_db_connection():
    """Returns a new database connection for the FastAPI routes."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

init_db()