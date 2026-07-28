import pandas as pd
import io
from frontend.views.database_view import prepare_csv_export_data

def test_prepare_csv_export_data_empty():
    assert prepare_csv_export_data(None) == b""
    assert prepare_csv_export_data(pd.DataFrame()) == b""

def test_prepare_csv_export_data_valid():
    data = [{
        'id': 'doc-123',
        'filename': 'invoice_001.pdf',
        'status': 'approved',
        'parsed_vendor': 'Acme Corp',
        'parsed_currency': '$',
        'parsed_tax': 10.50,
        'parsed_total': 110.50,
        'overall_confidence': 0.98,
        'created_at': '2026-07-28T10:00:00Z'
    }]
    df = pd.DataFrame(data)
    csv_bytes = prepare_csv_export_data(df)
    
    assert isinstance(csv_bytes, bytes)
    content = csv_bytes.decode('utf-8')
    assert "ID,Filename,Status,Vendor,Currency,Tax Amount,Total Amount,Confidence,Created At" in content
    assert "doc-123,invoice_001.pdf,approved,Acme Corp,$,10.5,110.5,0.98,2026-07-28T10:00:00Z" in content
