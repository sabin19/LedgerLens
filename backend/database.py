import sqlite3
import os

DB_NAME = "ledgerlens.db"
UPLOADS_DIR = "uploads"

def init_db():
    """Initializes the database and local storage directory."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            status TEXT NOT NULL,
            extracted_json TEXT,
            reviewed_json TEXT,
            overall_confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Returns a new database connection for the FastAPI routes."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

init_db()