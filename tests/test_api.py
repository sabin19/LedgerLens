import requests
from PIL import Image, ImageDraw

def create_dummy_receipt(filename="dummy_receipt.jpg"):
    """Creates a basic image resembling a receipt."""
    img = Image.new('RGB', (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    text = (
        "VENDOR: ACME Supplies\n"
        "DATE: 2026-07-22\n\n"
        "1x Server Rack    $450.00\n"
        "2x Ethernet Cable $20.00\n\n"
        "TAX: $47.00\n"
        "TOTAL: $517.00"
    )
    draw.text((20, 20), text, fill=(0, 0, 0))
    img.save(filename)
    return filename

def test_ingest_endpoint():
    """Sends the dummy receipt to the local FastAPI server."""
    url = "http://localhost:8000/ingest"
    filename = create_dummy_receipt()
    
    print(f"Uploading {filename} to {url}...")
    
    with open(filename, "rb") as f:
        # Define the multipart/form-data payload
        files = {"file": (filename, f, "image/jpeg")}
        
        try:
            response = requests.post(url, files=files)
            
            print(f"\n--- Response (Status: {response.status_code}) ---")
            if response.status_code == 200:
                import json
                print(json.dumps(response.json(), indent=2))
            else:
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("\nError: Could not connect to the server. Is FastAPI running on port 8000?")

if __name__ == "__main__":
    test_ingest_endpoint()