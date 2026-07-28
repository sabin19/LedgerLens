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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Migration: Check existing columns using PRAGMA
    cursor.execute("PRAGMA table_info(documents)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # 3. Add updated_at if it's missing (Using the SQLite table-recreation workaround)
    if 'updated_at' not in columns:
        print("Migration: Adding 'updated_at' column to 'documents' table via recreation...")
        
        # A. Create a new table with the updated schema
        cursor.execute('''
            CREATE TABLE documents_new (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                extracted_json TEXT,
                reviewed_json TEXT,
                overall_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # B. Copy data from the old table to the new one 
        # (updated_at will automatically take CURRENT_TIMESTAMP for the copied rows)
        cursor.execute('''
            INSERT INTO documents_new 
            (id, filename, status, extracted_json, reviewed_json, overall_confidence, created_at)
            SELECT id, filename, status, extracted_json, reviewed_json, overall_confidence, created_at 
            FROM documents
        ''')
        
        # C. Drop the old table
        cursor.execute("DROP TABLE documents")
        
        # D. Rename the new table to the original name
        cursor.execute("ALTER TABLE documents_new RENAME TO documents")
        
    conn.commit()
    conn.close()

def get_db_connection():
    """Returns a new database connection for the FastAPI routes."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

init_db()