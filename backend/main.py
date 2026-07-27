import base64
import json
import re
import uuid
import datetime
import os
import time
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image, ImageDraw
import openai
from openai import OpenAI, RateLimitError
from fastapi.staticfiles import StaticFiles
from streamlit import status


# Import the database and schema modules you just created
from backend.database import get_db_connection
from backend.schemas import InvoiceSchema
import time # Ensure this is imported for latency tracking
from prometheus_client import Counter, Histogram, make_asgi_app

app = FastAPI(title="LedgerLens API")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Note: max_retries handles 5xx and dropouts, but does NOT resolve 429 TPM exhaustion natively
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "4")),
)
REVIEW_THRESHOLD = 0.90

# --- PROMETHEUS METRICS ---
# Histograms track latency distributions
EXTRACTION_LATENCY = Histogram("extraction_latency_seconds", "Time spent extracting data via vision model")
MODERATION_LATENCY = Histogram("moderation_latency_seconds", "Time spent in the moderation gate")

# Counters track cumulative totals
TOKEN_COST_USD = Counter("token_cost_usd", "Estimated token cost in USD")
AUTO_APPROVALS = Counter("auto_approvals_total", "Total documents automatically approved")
DOCS_PROCESSED = Counter("throughput_docs_total", "Total documents processed")

# Mount the Prometheus ASGI app to expose the /metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Cost approximation (GPT-4o-mini is roughly $0.15 per 1M input / $0.60 per 1M output)
# We will use a blended average for this MVP metric of $0.0000003 per token
ESTIMATED_COST_PER_TOKEN = 0.0000003


def call_openai_with_backoff(api_func, *args, max_retries=5, initial_delay=2, **kwargs):
    """Executes an OpenAI API method using an exponential backoff loop for 429s."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return api_func(*args, **kwargs)
        except RateLimitError as error:
            if attempt == max_retries - 1:
                # Exhausted retries, convert to the application's clean HTTP exception
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "The OpenAI API rate limit was reached. Wait a moment and retry. "
                        "If this continues, check the project's usage limits and billing."
                    ),
                    headers={"Retry-After": str(int(delay))},
                ) from error
            
            # Back off and wait before trying again
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            # Propagate any other unexpected OpenAI exceptions immediately
            raise e

def redact_pii(text: str) -> str:
    """Regex patterns to redact PII from the extracted JSON string."""
    # SSN (US)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED]', text) 
    
    # Email
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED]', text) 
    
    # Phone Numbers (Safer regex that avoids catching dates)
    # Looks for optional country code, optional parentheses, and standard spacing/hyphens
    text = re.sub(r'(?<!\d)(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)', '[REDACTED]', text)
    
    return text

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    # 1. Read raw image into PIL memory buffer first
    image_bytes = await file.read()
    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file format.")

    # 2. Downscale immediately to optimize TPM (Tokens Per Minute) usage
    # Downscaling to max 1024x1024 preserves receipt text readability but decimates token consumption
    img.thumbnail((1024, 1024))
    
    # Render downscaled image to web-ready JPEG payload strings
    buffered = BytesIO()
    # Save using standard formats to maximize compatibility with vision engines
    img.save(buffered, format="JPEG", quality=85) 
    optimized_bytes = buffered.getvalue()
    
    b64_str = base64.b64encode(optimized_bytes).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{b64_str}"
    mod_start_time = time.time()
    # 3. Moderation Gate using Downscaled URI and Backoff Strategy
    mod_response = call_openai_with_backoff(
        client.moderations.create,
        model="omni-moderation-latest",
        input=[{"type": "image_url", "image_url": {"url": data_uri}}]
    )
    MODERATION_LATENCY.observe(time.time() - mod_start_time) # Record latency
    
    if mod_response.results[0].flagged:
        raise HTTPException(status_code=422, detail={"blocked_reason": "Image content flagged by moderation gate."})

    # 4. Watermark Production Data
    doc_id = str(uuid.uuid4())
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"{doc_id} | {datetime.datetime.now().isoformat()}", fill="gray")
    
    # Save the watermarked image to local asset directory
    os.makedirs(f"uploads/{doc_id}", exist_ok=True)
    img.save(f"uploads/{doc_id}/watermarked.png")
    ext_start_time = time.time()
    # 5. Structured Vision Extraction with Backoff Strategy
    completion = call_openai_with_backoff(
        client.chat.completions.parse,
        model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the structured data from this invoice/receipt."},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ],
        response_format=InvoiceSchema
    )
    EXTRACTION_LATENCY.observe(time.time() - ext_start_time) # Record latency

    # Track Token Cost
    usage = getattr(completion, "usage", None)
    if usage and hasattr(usage, "total_tokens"):
        TOKEN_COST_USD.inc(usage.total_tokens * ESTIMATED_COST_PER_TOKEN)
    
# Assertions satisfy Pylance's type checker and provide a runtime safety net
    assert completion is not None, "OpenAI API returned an empty response."
    assert completion.choices[0].message.parsed is not None, "Failed to parse the schema."

    parsed_schema = completion.choices[0].message.parsed
    extracted_data = parsed_schema.model_dump()
    extracted_json_str = parsed_schema.model_dump_json()

    
    # 6. Confidence Routing
    overall_conf = extracted_data.get('overall_confidence', 1.0)
    status = "auto_approved"
    if extracted_data.get('overall_confidence', 1.0) < REVIEW_THRESHOLD:
        status = "pending_review"
    else:
        for item in extracted_data.get('line_items', []):
            if item.get('confidence', 1.0) < REVIEW_THRESHOLD:
                status = "pending_review"
                break
                
    # 7. PII Redaction
    safe_json = redact_pii(extracted_json_str)
    
    # 8. Database Persistence
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO documents (id, filename, status, extracted_json, overall_confidence) VALUES (?, ?, ?, ?, ?)",
        (doc_id, file.filename, status, safe_json, overall_conf)
    )
    conn.commit()
    conn.close()
    # Record Prometheus throughput and approval metrics
    DOCS_PROCESSED.inc()
    if status == "auto_approved":
        AUTO_APPROVALS.inc()
    
    return {"doc_id": doc_id, "status": status, "data": extracted_data}

@app.get("/review")
def get_review_queue():
    """Fetches all documents that were flagged for human review."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM documents WHERE status = 'pending_review'").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/approve")
def approve_document(doc_id: str, corrected_data: dict):
    """Commits human reviewer corrections and marks the document as approved."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE documents SET status = 'auto_approved', reviewed_json = ? WHERE id = ?",
        (json.dumps(corrected_data), doc_id)
    )
    conn.commit()
    conn.close()
    return {"status": "success", "doc_id": doc_id}

@app.get("/documents")
def get_all_documents():
    """Fetches all documents from the database for the frontend table."""
    conn = get_db_connection()
    # Order by newest first
    rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}   
