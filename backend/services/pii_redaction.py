import re

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