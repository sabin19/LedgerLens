import pytest
from pydantic import ValidationError
from backend.schemas import InvoiceSchema, LineItem

# --- Fixtures ---
@pytest.fixture
def valid_invoice_data():
    """Provides a valid dictionary representing extracted invoice data."""
    return {
        "vendor": "Acme Corp",
        "invoice_number": "INV-10023",
        "date": "2026-07-26",
        "currency": "USD",
        "subtotal": 100.0,
        "tax": 5.0,
        "total": 105.0,
        "overall_confidence": 0.95,
        "line_items": [
            {
                "description": "Server Rack",
                "quantity": 1.0,
                "unit_price": 100.0,
                "amount": 100.0,
                "confidence": 0.92
            }
        ]
    }

# --- Tests ---
def test_invoice_schema_accepts_valid_data(valid_invoice_data):
    """Test that the schema successfully parses a perfectly formatted payload."""
    invoice = InvoiceSchema(**valid_invoice_data)
    
    assert invoice.vendor == "Acme Corp"
    assert invoice.total == 105.0
    assert len(invoice.line_items) == 1
    assert invoice.line_items[0].description == "Server Rack"

def test_invoice_schema_requires_mandatory_fields(valid_invoice_data):
    """Test that missing mandatory fields (like 'total') throw a ValidationError."""
    invalid_data = valid_invoice_data.copy()
    del invalid_data["total"] # Remove a required field
    
    with pytest.raises(ValidationError) as excinfo:
        InvoiceSchema(**invalid_data)
        
    assert "total" in str(excinfo.value)

def test_invoice_schema_allows_optional_fields(valid_invoice_data):
    """Test that optional fields (like 'invoice_number' and 'tax') can be None."""
    data_missing_optionals = valid_invoice_data.copy()
    data_missing_optionals["invoice_number"] = None
    data_missing_optionals["tax"] = None
    
    invoice = InvoiceSchema(**data_missing_optionals)
    
    assert invoice.invoice_number is None
    assert invoice.tax is None
    assert invoice.total == 105.0 # Required field remains intact

def test_invoice_schema_json_roundtrip(valid_invoice_data):
    """Test that the schema can serialize to JSON and deserialize back perfectly."""
    # 1. Load into Pydantic model
    original_invoice = InvoiceSchema(**valid_invoice_data)
    
    # 2. Serialize to JSON string
    json_string = original_invoice.model_dump_json()
    
    # 3. Deserialize back to Pydantic model
    reconstructed_invoice = InvoiceSchema.model_validate_json(json_string)
    
    # 4. Assert they are identical
    assert original_invoice == reconstructed_invoice