import pytest
from frontend.views.ingestion import render_extraction_dashboard

def test_render_extraction_dashboard_handles_invalid_inputs():
    # Should safely return without crashing for invalid inputs
    render_extraction_dashboard(None)
    render_extraction_dashboard("invalid string")
    render_extraction_dashboard({})

def test_render_extraction_dashboard_runs_with_sample_invoice(monkeypatch):
    # Mock streamlit components to verify render completes cleanly without error
    sample_data = {
        "vendor": "Acme Supplies",
        "invoice_number": "INV-2026-001",
        "date": "2026-07-29",
        "currency": "USD",
        "subtotal": 100.0,
        "tax": 10.0,
        "total": 110.0,
        "overall_confidence": 0.95,
        "line_items": [
            {
                "description": "Paper Reams",
                "quantity": 5,
                "unit_price": 20.0,
                "amount": 100.0,
                "confidence": 0.98
            }
        ]
    }
    
    # Execution should pass smoothly
    render_extraction_dashboard(sample_data)
