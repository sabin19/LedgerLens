import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

def fetch_documents():
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None

def fetch_review_queue():
    try:
        response = requests.get(f"{API_BASE_URL}/review")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None

def upload_document(files):
    try:
        response = requests.post(f"{API_BASE_URL}/ingest", files=files)
        return response.status_code, response.json() if response.status_code == 200 else response.text
    except requests.exceptions.ConnectionError:
        return 503, "Connection Error"

def approve_document(doc_id, edited_data):
    try:
        response = requests.post(f"{API_BASE_URL}/approve", params={"doc_id": doc_id}, json=edited_data)
        return response.status_code
    except requests.exceptions.ConnectionError:
        return 503

def fetch_watermarked_image(doc_id):
    image_url = f"{API_BASE_URL}/uploads/{doc_id}/watermarked.png"
    try:
        response = requests.get(image_url)
        return response.status_code, response.content
    except Exception as e:
        return 500, str(e)