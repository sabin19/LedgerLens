import json
from backend.database.config import get_db_connection

def create_document(doc_id: str, filename: str, status: str, safe_json: str, overall_conf: float, perceptual_hash: str = None):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO documents (id, filename, status, extracted_json, overall_confidence, perceptual_hash) VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, filename, status, safe_json, overall_conf, perceptual_hash)
    )
    conn.commit()
    conn.close()

def get_all_perceptual_hashes():
    conn = get_db_connection()
    rows = conn.execute("SELECT id, filename, perceptual_hash FROM documents WHERE perceptual_hash IS NOT NULL").fetchall()
    conn.close()
    return [dict(row) for row in rows]

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