import pytest
from fastapi import HTTPException
from frontend.views.review_queue import validate_review_payload
from backend.api.routes import validate_human_corrected_data

def test_validate_review_payload_valid():
    is_valid, msg = validate_review_payload(
        vendor="Acme Corp",
        inv_num="INV-1001",
        date_str="2026-07-28",
        currency="USD",
        subtotal=100.0,
        tax=10.0,
        total=110.0,
        updated_line_items=[
            {"description": "Item 1", "quantity": 1, "unit_price": 100.0, "amount": 100.0, "confidence": 1.0}
        ]
    )
    assert is_valid is True
    assert msg == ""

def test_validate_review_payload_empty_vendor():
    is_valid, msg = validate_review_payload(
        vendor="  ",
        inv_num="INV-1001",
        date_str="2026-07-28",
        currency="USD",
        subtotal=100.0,
        tax=10.0,
        total=110.0,
        updated_line_items=[
            {"description": "Item 1", "quantity": 1, "unit_price": 100.0, "amount": 100.0, "confidence": 1.0}
        ]
    )
    assert is_valid is False
    assert "Vendor" in msg

def test_validate_review_payload_null_line_item_field():
    is_valid, msg = validate_review_payload(
        vendor="Acme Corp",
        inv_num="INV-1001",
        date_str="2026-07-28",
        currency="USD",
        subtotal=100.0,
        tax=10.0,
        total=110.0,
        updated_line_items=[
            {"description": "", "quantity": 1, "unit_price": 100.0, "amount": 100.0, "confidence": 1.0}
        ]
    )
    assert is_valid is False
    assert "Description" in msg

def test_backend_validate_human_corrected_data_valid():
    valid_payload = {
        "vendor": "Acme Corp",
        "invoice_number": "INV-1001",
        "date": "2026-07-28",
        "currency": "USD",
        "subtotal": 100.0,
        "tax": 10.0,
        "total": 110.0,
        "line_items": [
            {"description": "Widget", "quantity": 2, "unit_price": 50.0, "amount": 100.0, "confidence": 0.99}
        ]
    }
    # Should not raise exception
    validate_human_corrected_data(valid_payload)

def test_backend_validate_human_corrected_data_invalid_null():
    invalid_payload = {
        "vendor": "Acme Corp",
        "invoice_number": "INV-1001",
        "date": "2026-07-28",
        "currency": "USD",
        "subtotal": None,
        "tax": 10.0,
        "total": 110.0,
        "line_items": [
            {"description": "Widget", "quantity": 2, "unit_price": 50.0, "amount": 100.0, "confidence": 0.99}
        ]
    }
    with pytest.raises(HTTPException) as exc:
        validate_human_corrected_data(invalid_payload)
    assert exc.value.status_code == 400
    assert "subtotal" in str(exc.value.detail)
