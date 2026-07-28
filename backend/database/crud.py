import json
from backend.database.config import get_db_connection

def create_document(doc_id: str, filename: str, status: str, safe_json: str, overall_conf: float):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO documents (id, filename, status, extracted_json, overall_confidence) VALUES (?, ?, ?, ?, ?)",
        (doc_id, filename, status, safe_json, overall_conf)
    )
    conn.commit()
    conn.close()

def get_pending_reviews():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM documents WHERE status = 'pending_review'").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_document_status(doc_id: str, corrected_data: dict):
    conn = get_db_connection()
    conn.execute(
        "UPDATE documents SET status = 'auto_approved', reviewed_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(corrected_data), doc_id)
    )
    conn.commit()
    conn.close()

def get_all_documents():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_for_review(doc_id: str):
    conn = get_db_connection()
    conn.execute(
        "UPDATE documents SET status = 'pending_review', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (doc_id,)
    )
    conn.commit()
    conn.close()