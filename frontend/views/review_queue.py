import streamlit as st
import pandas as pd
import json
from frontend.services import api_client

import math

def is_null_or_empty(val):
    if val is None or pd.isna(val):
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    if isinstance(val, str) and not val.strip():
        return True
    return False

def validate_review_payload(vendor, inv_num, date_str, currency, subtotal, tax, total, updated_line_items):
    """
    Validates human input for review queue approval. Returns (is_valid: bool, error_message: str).
    Ensures no null, None, NaN, or empty values anywhere in human input.
    """
    if is_null_or_empty(vendor):
        return False, "Vendor / Merchant Name cannot be null or empty."
    if is_null_or_empty(inv_num):
        return False, "Invoice Number cannot be null or empty."
    if is_null_or_empty(date_str):
        return False, "Date cannot be null or empty."
    if is_null_or_empty(currency):
        return False, "Currency Code cannot be null or empty."
    if is_null_or_empty(subtotal):
        return False, "Subtotal amount cannot be null or empty."
    if is_null_or_empty(tax):
        return False, "Tax amount cannot be null or empty."
    if is_null_or_empty(total):
        return False, "Total amount cannot be null or empty."

    if not isinstance(updated_line_items, list) or len(updated_line_items) == 0:
        return False, "At least one line item is required."

    for idx, item in enumerate(updated_line_items, start=1):
        if not isinstance(item, dict):
            return False, f"Line item #{idx} is invalid."
        for key, val in item.items():
            if is_null_or_empty(val):
                readable_key = key.replace('_', ' ').title()
                return False, f"Line item #{idx} column '{readable_key}' cannot be null or empty."

    return True, ""

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
                st.caption("💡 *Tip: You can edit cells, select the checkbox on the left of any row and press Delete, or use the **Remove Row** selector below.*")
                
                line_items_state_key = f"line_items_df_{doc_id}"
                if line_items_state_key not in st.session_state:
                    raw_line_items = extracted_data.get('line_items', [])
                    if not isinstance(raw_line_items, list):
                        raw_line_items = []
                    line_items_df = pd.DataFrame(raw_line_items)
                    if line_items_df.empty:
                        line_items_df = pd.DataFrame(columns=["description", "quantity", "unit_price", "amount", "confidence"])
                    st.session_state[line_items_state_key] = line_items_df

                edited_line_items_df = st.data_editor(
                    st.session_state[line_items_state_key],
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"line_items_editor_{doc_id}"
                )
                st.session_state[line_items_state_key] = edited_line_items_df

                if not edited_line_items_df.empty:
                    del_col1, del_col2 = st.columns([3, 1])
                    with del_col1:
                        row_options = list(range(1, len(edited_line_items_df) + 1))
                        def format_row_label(i):
                            desc = edited_line_items_df.iloc[i-1].get('description', '')
                            desc_str = f" ({desc})" if desc and pd.notna(desc) else ""
                            return f"Row #{i}{desc_str}"

                        selected_row_idx = st.selectbox(
                            "Select row to remove:",
                            options=row_options,
                            format_func=format_row_label,
                            key=f"select_del_row_{doc_id}"
                        )
                    with del_col2:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️ Remove Row", key=f"btn_del_row_{doc_id}", type="secondary", use_container_width=True):
                            if 1 <= selected_row_idx <= len(edited_line_items_df):
                                new_df = edited_line_items_df.drop(edited_line_items_df.index[selected_row_idx - 1]).reset_index(drop=True)
                                st.session_state[line_items_state_key] = new_df
                                st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ Approve & Save Corrections", key=f"btn_approve_{doc_id}", type="primary", use_container_width=True):
                    # Convert edited DataFrame back to list of dicts
                    try:
                        updated_line_items = edited_line_items_df.to_dict(orient="records")
                    except Exception:
                        updated_line_items = raw_line_items

                    # Validate human input before proceeding
                    is_valid, err_msg = validate_review_payload(
                        vendor=new_vendor,
                        inv_num=new_inv_num,
                        date_str=new_date,
                        currency=new_currency,
                        subtotal=new_subtotal,
                        tax=new_tax,
                        total=new_total,
                        updated_line_items=updated_line_items
                    )

                    if not is_valid:
                        st.error(f"❌ Cannot approve submission: {err_msg}")
                    else:
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