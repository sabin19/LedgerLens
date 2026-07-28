from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

# Import the centralized router
from backend.api import routes

app = FastAPI(title="Invoice Lense API")

# Mount static assets
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Register all API endpoints
app.include_router(routes.router)