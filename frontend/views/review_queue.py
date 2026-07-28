import streamlit as st
import pandas as pd
import json
from frontend.services import api_client

def render_review_queue():
    st.markdown("### ✍️ Human Review Queue")
    st.markdown("Inspect documents flagged for review, correct extracted metadata or line items, and commit to database.")
    st.divider()
    
    queue = api_client.fetch_review_queue()
    
    if queue is None:
        st.error("Failed to connect to backend. Is the FastAPI server running?")
        return
        
    if not queue:
        st.info("🎉 All caught up! No documents pending review.")
        return
        
    for doc in queue:
        doc_id = doc['id']
        filename = doc.get('filename', 'Unknown Document')
        conf = doc.get('overall_confidence', 0.0)
        conf_percent = f"{float(conf)*100:.0f}%" if conf is not None else "N/A"
        
        with st.expander(f"📋 {filename} (ID: {doc_id}) — AI Confidence: {conf_percent}", expanded=True):
            # Parse existing JSON data
            raw_json = doc.get('extracted_json', '{}')
            try:
                extracted_data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                if not isinstance(extracted_data, dict):
                    extracted_data = {}
            except Exception:
                extracted_data = {}

            img_col, form_col = st.columns([1, 1], gap="medium")
            
            # --- LEFT COLUMN: Watermarked Document Image Preview ---
            with img_col:
                st.markdown("#### 🖼️ Document Preview")
                status_code, img_bytes = api_client.fetch_watermarked_image(doc_id)
                if status_code == 200 and isinstance(img_bytes, bytes):
                    st.image(img_bytes, use_container_width=True)
                else:
                    st.warning("Original image preview unavailable.")
            
            # --- RIGHT COLUMN: Form & Data Editors ---
            with form_col:
                st.markdown("#### 📝 Edit Extracted Metadata")
                
                # Top-level metadata fields
                vendor_val = extracted_data.get('vendor_name', extracted_data.get('vendor', ''))
                inv_num_val = extracted_data.get('invoice_number', '')
                date_val = extracted_data.get('date', '')
                currency_val = extracted_data.get('currency', 'USD')
                
                subtotal_val = float(extracted_data.get('subtotal') or 0.0)
                tax_val = float(extracted_data.get('tax') or extracted_data.get('tax_amount') or 0.0)
                total_val = float(extracted_data.get('total') or extracted_data.get('total_amount') or 0.0)

                col_a, col_b = st.columns(2)
                with col_a:
                    new_vendor = st.text_input("Vendor / Merchant Name", value=str(vendor_val), key=f"v_{doc_id}")
                    new_inv_num = st.text_input("Invoice Number", value=str(inv_num_val or ''), key=f"inv_{doc_id}")
                    new_subtotal = st.number_input("Subtotal", value=subtotal_val, step=0.01, key=f"sub_{doc_id}")
                    new_total = st.number_input("Total Amount", value=total_val, step=0.01, key=f"tot_{doc_id}")
                
                with col_b:
                    new_date = st.text_input("Date (YYYY-MM-DD)", value=str(date_val or ''), key=f"dt_{doc_id}")
                    new_currency = st.text_input("Currency Code", value=str(currency_val or 'USD'), key=f"cur_{doc_id}")
                    new_tax = st.number_input("Tax Amount", value=tax_val, step=0.01, key=f"tx_{doc_id}")

                st.markdown("#### 🛒 Line Items")
                raw_line_items = extracted_data.get('line_items', [])
                if not isinstance(raw_line_items, list):
                    raw_line_items = []
                    
                line_items_df = pd.DataFrame(raw_line_items)
                if line_items_df.empty:
                    line_items_df = pd.DataFrame(columns=["description", "quantity", "unit_price", "amount", "confidence"])

                edited_line_items_df = st.data_editor(
                    line_items_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"line_items_editor_{doc_id}"
                )

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ Approve & Save Corrections", key=f"btn_approve_{doc_id}", type="primary", use_container_width=True):
                    # Convert edited DataFrame back to list of dicts
                    try:
                        updated_line_items = edited_line_items_df.to_dict(orient="records")
                    except Exception:
                        updated_line_items = raw_line_items

                    # Construct updated JSON payload
                    corrected_payload = {
                        "vendor": new_vendor,
                        "vendor_name": new_vendor,
                        "invoice_number": new_inv_num,
                        "date": new_date,
                        "currency": new_currency,
                        "subtotal": new_subtotal,
                        "tax": new_tax,
                        "tax_amount": new_tax,
                        "total": new_total,
                        "total_amount": new_total,
                        "line_items": updated_line_items,
                        "overall_confidence": extracted_data.get("overall_confidence", 1.0)
                    }

                    status = api_client.approve_document(doc_id, corrected_payload)
                    if status == 200:
                        st.toast(f"✅ Approved '{filename}' and updated database!")
                        st.rerun()
                    else:
                        st.error(f"Failed to approve document (Status Code: {status}).")