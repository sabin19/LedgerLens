import base64
import uuid
import datetime
import os
import time
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, ImageDraw
from prometheus_client import Counter, Histogram

# Import our new isolated services
from backend.services.vision import moderate_image, extract_invoice_data
from backend.services.pii_redaction import redact_pii
from backend.database import crud

router = APIRouter()

# --- PROMETHEUS METRICS ---
EXTRACTION_LATENCY = Histogram("extraction_latency_seconds", "Time spent extracting data")
MODERATION_LATENCY = Histogram("moderation_latency_seconds", "Time spent in moderation")
TOKEN_COST_USD = Counter("token_cost_usd", "Estimated token cost in USD")
AUTO_APPROVALS = Counter("auto_approvals_total", "Total documents automatically approved")
DOCS_PROCESSED = Counter("throughput_docs_total", "Total documents processed")
ESTIMATED_COST_PER_TOKEN = 0.0000003
REVIEW_THRESHOLD = 0.95

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    image_bytes = await file.read()
    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file format.")

    img.thumbnail((1024, 1024))
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=85) 
    b64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{b64_str}"
    
    mod_start_time = time.time()
    mod_response = moderate_image(data_uri)
    MODERATION_LATENCY.observe(time.time() - mod_start_time)

    assert mod_response is not None, "Moderation API returned an empty response."
    
    if mod_response.results[0].flagged:
        raise HTTPException(status_code=422, detail={"blocked_reason": "Flagged by moderation."})

    doc_id = str(uuid.uuid4())
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"{doc_id} | {datetime.datetime.now().isoformat()}", fill="gray")
    os.makedirs(f"uploads/{doc_id}", exist_ok=True)
    img.save(f"uploads/{doc_id}/watermarked.png")
    
    ext_start_time = time.time()
    completion = extract_invoice_data(data_uri)
    EXTRACTION_LATENCY.observe(time.time() - ext_start_time)

    usage = getattr(completion, "usage", None)
    if usage and hasattr(usage, "total_tokens"):
        TOKEN_COST_USD.inc(usage.total_tokens * ESTIMATED_COST_PER_TOKEN)
    
    assert completion is not None, "OpenAI API returned an empty response."
    assert completion.choices[0].message.parsed is not None, "Failed to parse the schema."

    parsed_schema = completion.choices[0].message.parsed
    extracted_data = parsed_schema.model_dump()
    extracted_json_str = parsed_schema.model_dump_json()

    # 1. Safely parse overall confidence
    raw_conf = extracted_data.get('overall_confidence')
    overall_conf = float(raw_conf) if raw_conf is not None else 1.0
        
    status = "auto_approved"
        
    if overall_conf < REVIEW_THRESHOLD:
        status = "pending_review"
    else:
        # 2. Use a Type Guard so Pylance knows this is definitively a list
        raw_items = extracted_data.get('line_items')
        line_items = raw_items if isinstance(raw_items, list) else []
            
        # 3. Use a standard loop with another Type Guard for the dictionaries
        for item in line_items:
            if isinstance(item, dict):
                raw_item_conf = item.get('confidence')
                item_conf = float(raw_item_conf) if raw_item_conf is not None else 1.0
                    
                if item_conf < REVIEW_THRESHOLD:
                    status = "pending_review"
                    break
                
    safe_json = redact_pii(extracted_json_str)
    # Provide a safe fallback if the HTTP request didn't include a filename
    safe_filename = file.filename or "unknown_document"
    crud.create_document(doc_id, safe_filename, status, safe_json, overall_conf)
    
    DOCS_PROCESSED.inc()
    if status == "auto_approved":
        AUTO_APPROVALS.inc()
    
    return {"doc_id": doc_id, "status": status, "data": extracted_data}

@router.get("/review")
def get_review_queue():
    return crud.get_pending_reviews()

@router.post("/approve")
def approve_document(doc_id: str, corrected_data: dict):
    crud.update_document_status(doc_id, corrected_data)
    return {"status": "success", "doc_id": doc_id}

@router.post("/move-to-review")
def move_to_review(doc_id: str):
    crud.mark_for_review(doc_id)
    return {"status": "success", "doc_id": doc_id}

@router.get("/documents")
def get_all_documents():
    return crud.get_all_documents()

@router.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}