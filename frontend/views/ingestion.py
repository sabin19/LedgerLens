import streamlit as st
import base64
from frontend.services import api_client
from frontend.components.dialogs import view_original_image_dialog

def render_ingestion():
    st.markdown("### 📄 Document Ingestion")
    st.markdown("Upload a receipt, invoice, or bill to automatically extract structured data using the vision engine.")
    st.divider()
    
    # CSS to style and add proper padding to the file uploader button and dropzone
    st.markdown("""
        <style>
            div[data-testid="stFileUploader"] { 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                padding-top: 120px; 
            }
            div[data-testid="stFileUploaderDropzone"] {
                padding: 1.25rem 1.75rem !important;
                border-radius: 12px !important;
            }
            div[data-testid="stFileUploader"] button,
            div[data-testid="stFileUploaderDropzone"] button,
            section[data-testid="stFileUploaderDropzone"] button,
            button[data-testid="baseButton-secondary"] {
                padding: 10px 24px !important;
                margin-right: 12px !important;
                border-radius: 8px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    preview_col, result_col = st.columns(2, gap="large")
    
    with preview_col:
        st.markdown("#### 🖼️ Document Preview")
        with st.container(height=600, border=True):
            if st.session_state.doc_image is None:
                uploaded_file = st.file_uploader("Upload Document", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
                if uploaded_file is not None:
                    st.session_state.doc_image = {
                        "name": uploaded_file.name, "type": uploaded_file.type,
                        "size": uploaded_file.size, "bytes": uploaded_file.getvalue()
                    }
                    st.rerun()
            else:
                doc = st.session_state.doc_image
                image_bytes = doc["bytes"]
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # 2. RESTORED: The HTML <img> tag that actually displays the picture
                st.markdown(f"""
                    <div style="display: flex; justify-content: center; align-items: center; height: 380px; margin-top: 10px;">
                        <img src="data:{doc['type']};base64,{b64_image}" style="max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px;">
                    </div>
                """, unsafe_allow_html=True)
                
                # Also added back the styling to center the text below the image
                st.markdown(f"<p style='text-align: center; color: gray; font-size: 14px; margin-top: 10px; margin-bottom: 15px;'><b>{doc['name']}</b> | {round(doc['size'] / 1024, 1)} KB</p>", unsafe_allow_html=True)
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("🔍 View Original", key="btn_view_original_ingest", use_container_width=True):
                        view_original_image_dialog(image_bytes)
                with btn_col2:
                    if st.button("❌ Remove Image", key="btn_remove_image_ingest", type="secondary", use_container_width=True):
                        st.session_state.doc_image = None
                        st.session_state.last_extraction_result = None
                        st.rerun()

    with result_col:
        st.markdown("#### 📊 Extraction Results")
        with st.container(height=600, border=True):
            if st.session_state.doc_image is not None:
                doc = st.session_state.doc_image
                threshold_pct = st.slider(
                    "🎯 Review Confidence Threshold (%)",
                    min_value=0,
                    max_value=100,
                    value=75,
                    step=1,
                    help="Extractions with overall or line-item confidence below this percentage (0-100%) will be flagged for manual review."
                )
                process_btn = st.button("🚀 Process Document", key="btn_process_document_ingest", type="primary", use_container_width=True)
                st.divider()
                
                if process_btn:
                    with st.spinner("Analyzing document with vision model..."):
                        files = {"file": (doc["name"], doc["bytes"], doc["type"])}
                        status_code, result = api_client.upload_document(files, review_threshold=threshold_pct / 100.0)
                        st.session_state.last_extraction_result = {"status_code": status_code, "result": result}

                res_info = st.session_state.get("last_extraction_result")
                if res_info:
                    status_code = res_info["status_code"]
                    result = res_info["result"]
                    
                    if status_code == 200 and isinstance(result, dict):
                        status = result.get('status', 'unknown')
                        data_obj = result.get("data", {})
                        doc_id = result.get("doc_id", "latest")
                        
                        if status == "auto_approved":
                            st.success(f"✅ Processed Successfully! (Status: {status})")
                            if st.button("➡️ Go to Database View", key=f"btn_nav_db_{doc_id}", type="primary", use_container_width=True):
                                st.session_state.switch_to_tab = 3
                                st.rerun()
                        elif status == "duplicate":
                            dup_of = result.get("duplicate_of", "N/A")
                            dist = result.get("hamming_distance", 0)
                            st.error(f"⚠️ Duplicate Document Detected! Matching Document ID: {dup_of[:8]}... (Distance: {dist})")
                            if st.button("➡️ View in Database", key=f"btn_nav_db_dup_{doc_id}", type="primary", use_container_width=True):
                                st.session_state.switch_to_tab = 3
                                st.rerun()
                        else:
                            st.warning(f"⚠️ Flagged for Review (Status: {status})")
                            if st.button("✍️ Go to Review Queue", key=f"btn_nav_rev_{doc_id}", type="primary", use_container_width=True):
                                st.session_state.switch_to_tab = 2
                                st.rerun()

                        st.json(data_obj)
                    elif status_code == 503:
                        st.error("Failed to connect to backend. Is the FastAPI server running?")
                    else:
                        st.error(f"Error {status_code}: {result}")
                elif not process_btn:
                    st.markdown("### 🤖 System Ready")
                    st.markdown("The Invoice Lense vision engine is standing by...")
                    st.info("👆 Click **Process Document** to begin extraction.")
            else:
                # Restored the empty state spacing
                st.markdown("<br><br><br><br><br><h4 style='text-align: center; color: #888;'>Waiting for Document</h4>", unsafe_allow_html=True)