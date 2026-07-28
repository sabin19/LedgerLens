import streamlit as st
import json
import pandas as pd
from frontend.services import api_client

@st.dialog("Document Photo", width="large")
def view_photo_dialog(doc_id):
    status, content = api_client.fetch_watermarked_image(doc_id)
    if status == 200:
        st.image(content, width="stretch")
    else:
        st.error(f"Failed to load image. (Error {status})")

@st.dialog("Extracted JSON Data", width="large")
def view_json_dialog(json_data):
    if not json_data or pd.isna(json_data):
        st.info("No JSON data available.")
        return
    try:
        parsed_data = json.loads(json_data) if isinstance(json_data, str) else json_data
        st.json(parsed_data)
    except Exception as e:
        st.error(f"Failed to parse JSON data: {str(e)}")

@st.dialog("Original Document View", width="large")
def view_original_image_dialog(image_bytes):
    st.image(image_bytes, width="stretch")