# LedgerLens - Submission Write-up

## What Shipped
Full document intelligence & receipt processing application built with a Streamlit frontend and FastAPI backend microservice architecture. Core features include:
- **Image Ingestion & Preprocessing**: Automatic JPEG compression (1024x1024) and audit watermarking (stamping document UUID and timestamp).
- **AI Extraction Engine**: Powered by OpenAI `gpt-4o-mini` vision model returning structured per-item and overall confidence scores.
- **Safety Moderation Gate**: Integrated `omni-moderation-latest` content screening prior to processing.
- **Duplicate Document Detection**: Computes a 64-bit Difference Hash (dHash) using PIL to calculate Hamming distance and detect duplicate uploaded invoices.
- **Privacy Enforcement**: Automated regex-based PII redaction for SSNs, credit cards, emails, and phone numbers before database persistence.
- **Dynamic Review Routing**: Configurable confidence threshold routing low-confidence documents or line items into a Human-in-the-Loop review queue.
- **Document Ledger & CSV Export**: Interactive searchable, filterable, and sortable database view with CSV export capability (`ledgerlens_database_export.csv`).
- **Observability & Metrics**: Prometheus metrics tracking extraction latency, moderation latency, throughput, auto-approvals, and estimated USD token cost.
- **Security & Infrastructure**: Access token environment protection gate and full Docker containerization (`docker-compose`).

## Key Technical Decisions
- **Structured Outputs via Pydantic (`chat.completions.parse`)**: Utilized OpenAI's native Pydantic schema validation (`InvoiceSchema`) over legacy function calling to guarantee strictly typed, validated JSON payloads with native error handling.
- **Decoupling UI & Backend Services**: Separated FastAPI backend routes (`backend/api/routes.py`), business logic (`backend/services/`), and SQLite persistence (`backend/database/`) from the Streamlit UI layer to allow independent unit testing and clean maintainability.
- **Image Preprocessing & Watermarking**: Resized and compressed image uploads to 1024x1024 JPEG before base64 encoding to minimize vision token consumption while applying audit watermarks.

## Stretch Goals Attempted
- **(Working) Duplicate-Invoice Detection via Perceptual Hash**: Computes 64-bit dHash for uploaded receipts and checks Hamming distance ($\le 5$) against stored document hashes — see [`backend/services/dedupe.py`](file:///Users/sabin/Development/antigravity/LedgerLens/backend/services/dedupe.py) & [`backend/api/routes.py`](file:///Users/sabin/Development/antigravity/LedgerLens/backend/api/routes.py#L35-L42).
- **(Working) Safety Moderation Gate**: Pre-screens uploaded documents for policy violations using `omni-moderation-latest` — see [`backend/services/vision.py`](file:///Users/sabin/Development/antigravity/LedgerLens/backend/services/vision.py#L30-L36) & [`backend/api/routes.py`](file:///Users/sabin/Development/antigravity/LedgerLens/backend/api/routes.py#L44-L51).
- **(Working) Automatic PII Masking**: Scrubs sensitive personal information (SSNs, credit cards, emails, phone numbers) before saving to database — see [`backend/services/pii_redaction.py`](file:///Users/sabin/Development/antigravity/LedgerLens/backend/services/pii_redaction.py).
- **(Working) Prometheus Observability & Cost Tracking**: Live metric instrumentation tracking latency, document volume, auto-approval rates, and estimated USD token expenditures — see [`backend/api/routes.py`](file:///Users/sabin/Development/antigravity/LedgerLens/backend/api/routes.py#L18-L25).
- **(Working) Database CSV Export**: Built-in CSV export button in Database View to download filtered document datasets — see [`frontend/views/database_view.py`](file:///Users/sabin/Development/antigravity/LedgerLens/frontend/views/database_view.py#L8-L24).
- **(Partial) Access Token Gate**: Environment token protection — see [`frontend/services/auth.py`](file:///Users/sabin/Development/antigravity/LedgerLens/frontend/services/auth.py); validates access tokens via Streamlit session state rather than full OAuth2/JWT framework.

## Known Limitations
- **Database Concurrency**: SQLite database storage (`ledgerlens.db`) limits high-concurrency concurrent write operations under parallel heavy load.
- **Single File Ingestion**: Ingests one document per request (no batch/ZIP file processing endpoint yet).
- **Static Regex PII Redaction**: Pattern-based PII redaction may miss non-standard PII formatting compared to ML-based named entity recognition (NER) models.
- **Local Media Storage**: Watermarked original images are stored on the local file system (`uploads/`) rather than cloud object storage (S3/GCS).
