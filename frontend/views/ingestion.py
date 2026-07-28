import streamlit as st
import base64
from frontend.services import api_client
from frontend.components.dialogs import view_original_image_dialog

def render_ingestion():
    st.markdown("### 📄 Document Ingestion")
    st.markdown("Upload a receipt, invoice, or bill to automatically extract structured data using the vision engine.")
    st.divider()
    
    # 1. RESTORED: CSS to center the file uploader and make it look like a neat button
    st.markdown("""
        <style>
            div[data-testid="stFileUploader"] { display: flex; justify-content: center; align-items: center; padding-top: 180px; }
            div[data-testid="stFileUploaderDropzone"] {
                width: 130px !important; height: 130px !important; background-color: #333333 !important; 
                border-radius: 12px !important; border: none !important; display: flex;
                justify-content: center; align-items: center; cursor: pointer; padding: 0 !important;
            }
            div[data-testid="stFileUploaderDropzone"]:hover { background-color: #444444 !important; }
            div[data-testid="stFileUploaderDropzone"] > div { display: none; }
            div[data-testid="stFileUploaderDropzone"]::after {
                content: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" height="42" viewBox="0 -960 960 960" width="42" fill="white"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h360v80H200v560h560v-360h80v360q0 33-23.5 56.5T760-120H200Zm40-160h480L570-480 450-320l-90-120-120 160Zm440-320v-80h-80v-80h80v-80h80v80h80v80h-80v80h-80Z"/></svg>');
                display: block;
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
                        st.rerun()

    with result_col:
        st.markdown("#### 📊 Extraction Results")
        with st.container(height=600, border=True):
            if st.session_state.doc_image is not None:
                doc = st.session_state.doc_image
                threshold_pct = st.slider(
                    "🎯 Review Threshold (%)",
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
                        
                        if status_code == 200 and isinstance(result, dict):
                            status = result.get('status', 'unknown')
                                
                            data_obj = result.get("data", {})
                            doc_id = result.get("doc_id")
                            raw_conf = data_obj.get("overall_confidence", 1.0)
                            try:
                                conf_val = float(raw_conf)
                            except (ValueError, TypeError):
                                conf_val = 1.0

                            if status == "auto_approved":
                                st.success(f"✅ Processed Successfully! (Status: {status})")
                            else:
                                st.warning(f"⚠️ Flagged for Review (Status: {status})")
                                
                            if conf_val < 0.95 and status != "pending_review" and doc_id:
                                if st.button("⚠️ Move to Review Queue", key=f"ingest_mov_{doc_id}", type="secondary"):
                                    res_code = api_client.move_to_review(doc_id)
                                    if res_code == 200:
                                        st.toast("✅ Moved document to Review Queue!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to update status in database.")

                            st.json(data_obj)
                        elif status_code == 503:
                            st.error("Failed to connect to backend. Is the FastAPI server running?")
                        else:
                            st.error(f"Error {status_code}: {result}")
                else:
                    st.markdown("### 🤖 System Ready")
                    st.markdown("The Invoice Lense vision engine is standing by...")
                    st.info("👆 Click **Process Document** to begin extraction.")
            else:
                # Restored the empty state spacing
                st.markdown("<br><br><br><br><br><h4 style='text-align: center; color: #888;'>Waiting for Document</h4>", unsafe_allow_html=True)