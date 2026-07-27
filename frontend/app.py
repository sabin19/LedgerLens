import streamlit as st
import requests
import json
import pandas as pd
import math
import sqlite3
import os


API_BASE_URL = "http://backend:8000"

st.set_page_config(layout="wide", page_title="LedgerLens")
st.title("LedgerLens Document Intelligence")

# --- POPUP DIALOG DEFINITIONS ---
@st.dialog("Document Photo", width="large")
def view_photo_dialog(doc_id):
    """Fetches and displays the watermarked image securely through the backend container."""
    # We use /uploads/ because FastAPI mounts the directory under this path
    image_url = f"{API_BASE_URL}/uploads/{doc_id}/watermarked.png"
    
    try:
        # 1. Fetch the image data server-to-server (bypasses Docker network issues)
        response = requests.get(image_url)
        
        if response.status_code == 200:
            # 2. Display the raw bytes directly and use the new width parameter to fix the warning
            st.image(response.content, width="stretch")
        else:
            st.error(f"Image not found. (Error {response.status_code})")
    except Exception as e:
        st.error(f"Failed to load image: {str(e)}")

@st.dialog("Extracted JSON Data", width="large")
def view_json_dialog(json_data):
    """Safely parses and displays JSON data."""
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
    """Displays the uncompressed original image in a popup."""
    # Updated to fix the Streamlit deprecation warning
    st.image(image_bytes, width="stretch")

# --- TOP NAVIGATION BAR ---
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Upload Document", "Review Queue", "Database View"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.markdown("### 📈 Executive Dashboard")
    st.markdown("Overview of processed documents, total spend, and automation performance.")
    
    # 1. Fetch live data from the backend
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            raw_data = response.json()
            dashboard_df = pd.DataFrame(raw_data)
        else:
            dashboard_df = pd.DataFrame()
    except Exception:
        dashboard_df = pd.DataFrame()

    if dashboard_df.empty:
        st.info("Upload your first document to populate the dashboard!")
    else:
        # 2. Safely parse the JSON strings to extract workable financial data
        totals = []
        vendors = []
        
        for _, row in dashboard_df.iterrows():
            json_str = row.get('extracted_json', '{}')
            try:
                data = json.loads(json_str) if isinstance(json_str, str) else json_str
            except:
                data = {}
            
            # Safely extract and clean total amount
            raw_total = data.get('total_amount', data.get('total', 0.0))
            if isinstance(raw_total, (int, float)):
                t = float(raw_total)
            else:
                t_str = str(raw_total).replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
                try:
                    t = float(t_str)
                except ValueError:
                    t = 0.0
            totals.append(t)
            
            # Extract vendor name
            v = data.get('vendor_name', data.get('vendor', 'Unknown'))
            vendors.append(v if v else "Unknown")
            
        # Add the parsed data to the dataframe for analysis
        dashboard_df['parsed_total'] = totals
        dashboard_df['parsed_vendor'] = vendors
        
        # 3. Calculate KPIs
        total_docs = len(dashboard_df)
        total_spend = sum(totals)
        
        approved_docs = len(dashboard_df[dashboard_df['status'] == 'auto_approved'])
        approval_rate = (approved_docs / total_docs) * 100 if total_docs > 0 else 0.0
        
        # 4. Render Metric Cards
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        
        with m1:
            with st.container(border=True):
                st.metric(label="Total Documents Processed", value=f"{total_docs}")
        with m2:
            with st.container(border=True):
                # Assuming USD as default for the global summary
                st.metric(label="Total Spend Processed", value=f"{total_spend:,.2f}")
        with m3:
            with st.container(border=True):
                st.metric(label="Straight-Through Processing", value=f"{approval_rate:.1f}%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 5. Render Charts
        chart_col1, chart_col2 = st.columns(2, gap="large")
        
        with chart_col1:
            st.markdown("#### 🏆 Top Vendors by Spend")
            with st.container(border=True):
                # Group by vendor, sum the totals, and get top 5
                vendor_spend = dashboard_df.groupby('parsed_vendor')['parsed_total'].sum().sort_values(ascending=False).head(5)
                if not vendor_spend.empty:
                    # Streamlit's native bar chart handles the Pandas Series automatically
                    st.bar_chart(vendor_spend, color="#4ade80")
                else:
                    st.write("Not enough data.")
                    
        with chart_col2:
            st.markdown("#### 🚦 Document Status Breakdown")
            with st.container(border=True):
                status_counts = dashboard_df['status'].value_counts()
                if not status_counts.empty:
                    st.bar_chart(status_counts, color="#60a5fa")
                else:
                    st.write("Not enough data.")

# --- TAB 2: INGESTION ---
with tab2:
    st.markdown("### 📄 Document Ingestion")
    st.markdown("Upload a receipt, invoice, or bill to automatically extract structured data using the vision engine.")
    st.divider()
    
    # --- CSS INJECTION: Moved outside the columns to fix top-alignment issues ---
    st.markdown("""
        <style>
            div[data-testid="stFileUploader"] {
                display: flex; justify-content: center; align-items: center; padding-top: 180px; 
            }
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

    # Initialize session state for the uploaded image
    if "doc_image" not in st.session_state:
        st.session_state.doc_image = None
    if "db_page" not in st.session_state:
        st.session_state.db_page = 1

    # Dual Column Layout
    preview_col, result_col = st.columns(2, gap="large")
    
    # --- LEFT COLUMN: IMAGE PLACEHOLDER & PREVIEW ---
    with preview_col:
        st.markdown("#### 🖼️ Document Preview")
        
        # FIXED HEIGHT CONTAINER (600px)
        with st.container(height=600, border=True):
            
            # STATE 1: Empty Placeholder
            if st.session_state.doc_image is None:
                uploaded_file = st.file_uploader("Upload Document", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
                
                if uploaded_file is not None:
                    st.session_state.doc_image = {
                        "name": uploaded_file.name,
                        "type": uploaded_file.type,
                        "size": uploaded_file.size,
                        "bytes": uploaded_file.getvalue()
                    }
                    st.rerun()
            
            # STATE 2: Image Viewer
            else:
                import base64
                
                doc = st.session_state.doc_image
                image_bytes = doc["bytes"]
                mime_type = doc["type"]
                
                # 1. Encode the raw, full-resolution image to Base64
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # 2. Use CSS to lock the height strictly to 380px. 
                st.markdown(f"""
                    <div style="display: flex; justify-content: center; align-items: center; height: 380px; margin-top: 10px;">
                        <img src="data:{mime_type};base64,{b64_image}" 
                             style="max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px;">
                    </div>
                """, unsafe_allow_html=True)
                
                file_size_kb = round(doc["size"] / 1024, 1)
                st.markdown(f"<p style='text-align: center; color: gray; font-size: 14px; margin-top: 10px; margin-bottom: 15px;'><b>{doc['name']}</b> | {file_size_kb} KB</p>", unsafe_allow_html=True)
                
                # Action Buttons
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("🔍 View Original", use_container_width=True):
                        view_original_image_dialog(image_bytes)
                with btn_col2:
                    if st.button("❌ Remove Image", type="secondary", use_container_width=True):
                        st.session_state.doc_image = None
                        st.rerun()

    # --- RIGHT COLUMN: EXTRACTION RESULTS ---
    with result_col:
        st.markdown("#### 📊 Extraction Results")
        
        with st.container(height=600, border=True):
            if st.session_state.doc_image is not None:
                doc = st.session_state.doc_image
                
                process_btn = st.button("🚀 Process Document", type="primary", use_container_width=True)
                st.divider()
                
                if process_btn:
                    with st.spinner("Analyzing document with vision model..."):
                        files = {"file": (doc["name"], doc["bytes"], doc["type"])}
                        try:
                            response = requests.post(f"{API_BASE_URL}/ingest", files=files)
                            if response.status_code == 200:
                                result = response.json()
                                status = result['status']
                                
                                if status == "auto_approved":
                                    st.success(f"✅ Processed Successfully! (Status: {status})")
                                else:
                                    st.warning(f"⚠️ Flagged for Review (Status: {status})")
                                
                                st.json(result["data"])
                            else:
                                st.error(f"Error {response.status_code}: {response.text}")
                        except requests.exceptions.ConnectionError:
                            st.error("Failed to connect to backend. Is the FastAPI server running?")
                else:
                    st.markdown("### 🤖 System Ready")
                    st.markdown("The LedgerLens vision engine is standing by to extract structured data from your document.")
                    st.markdown("""
                    **Target Data Points:**
                    *   🏢 Vendor Name
                    *   📅 Date & Invoice Number
                    *   💰 Total, Subtotal & Tax
                    *   🛒 Individual Line Items
                    """)
                    st.info("👆 Click **Process Document** to begin extraction.")
                    
            else:
                st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
                st.markdown("<h4 style='text-align: center; color: #888;'>Waiting for Document</h4>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #888;'>Upload a receipt or invoice on the left to begin.</p>", unsafe_allow_html=True)

# --- TAB 3: REVIEW QUEUE ---
with tab3:
    st.header("Human Review Queue")
    try:
        response = requests.get(f"{API_BASE_URL}/review")
        if response.status_code == 200:
            queue = response.json()
            if not queue:
                st.info("All caught up! No documents pending review.")
            else:
                for doc in queue:
                    with st.expander(f"Pending: {doc['filename']} (ID: {doc['id']})", expanded=True):
                        extracted_data = json.loads(doc['extracted_json'])
                        st.write("Correct any inaccurate fields below:")
                        edited_data = st.data_editor(extracted_data, key=f"editor_{doc['id']}", use_container_width=True)
                        
                        if st.button("Approve Corrections", key=f"btn_{doc['id']}"):
                            approve_res = requests.post(
                                f"{API_BASE_URL}/approve",
                                params={"doc_id": doc['id']},
                                json=edited_data
                            )
                            if approve_res.status_code == 200:
                                st.success("Document approved and committed to storage!")
                                st.rerun()
        else:
            st.error(f"Failed to fetch review queue: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to backend. Is the FastAPI server running?")

# --- TAB 4: DATABASE ---
with tab4:
    st.markdown("### 🗄️ Document Database")
    st.markdown("Review and manage all extracted documents.")
    
    # Fetch from Backend API
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
        else:
            df = pd.DataFrame()
    except Exception:
        st.error("Failed to connect to backend API.")
        df = pd.DataFrame()

    if df.empty:
        st.info("No documents found in the database yet.")
    else:
        # --- PAGINATION LOGIC ---
        ITEMS_PER_PAGE = 10
        total_items = len(df)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
        
        if st.session_state.db_page > total_pages:
            st.session_state.db_page = total_pages
            
        start_idx = (st.session_state.db_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_df = df.iloc[start_idx:end_idx]

        # --- CUSTOM TABLE HEADER ---
        with st.container(border=True):
            
            col_ratios = [2.2, 1.1, 1.8, 0.9, 0.9, 1.1, 1.5]
            
            h_cols = st.columns(col_ratios)
            h_cols[0].markdown("<div style='text-align: center; font-size: 14px;'><b>Filename</b></div>", unsafe_allow_html=True)
            h_cols[1].markdown("<div style='text-align: center; font-size: 14px;'><b>Status</b></div>", unsafe_allow_html=True)
            h_cols[2].markdown("<div style='text-align: center; font-size: 14px;'><b>Vendor Name</b></div>", unsafe_allow_html=True)
            h_cols[3].markdown("<div style='text-align: center; font-size: 14px;'><b>Tax</b></div>", unsafe_allow_html=True)
            h_cols[4].markdown("<div style='text-align: center; font-size: 14px;'><b>Total</b></div>", unsafe_allow_html=True)
            h_cols[5].markdown("<div style='text-align: center; font-size: 14px;'><b>Conf.</b></div>", unsafe_allow_html=True)
            h_cols[6].markdown("<div style='text-align: center; font-size: 14px;'><b>Actions</b></div>", unsafe_allow_html=True)
            st.divider()
            
            # --- CUSTOM TABLE ROWS ---
            for index, row in page_df.iterrows():
                
                r_cols = st.columns(col_ratios, vertical_alignment="center")
                
                fname = row.get('filename', 'Unknown')
                if len(fname) > 25:
                    fname = fname[:22] + "..."
                r_cols[0].markdown(f"<div style='text-align: center; font-size: 13px; color: #d1d5db;'>{fname}</div>", unsafe_allow_html=True)
                
                status = row.get('status', 'pending')
                status_color = "#4ade80" if status == 'auto_approved' else "#facc15"
                status_text = "Approved" if status == 'auto_approved' else "Review"
                r_cols[1].markdown(f"<div style='text-align: center; font-size: 13px; font-weight: bold; color: {status_color};'>{status_text}</div>", unsafe_allow_html=True)
                    
                json_str = row.get('extracted_json', '{}')
                if pd.isna(json_str) or not json_str:
                    json_str = '{}'
                
                try:
                    parsed_json = json.loads(json_str)
                except:
                    parsed_json = {}

                vendor = parsed_json.get('vendor_name', parsed_json.get('vendor', 'N/A'))
                if not vendor: 
                    vendor = 'N/A'
                r_cols[2].markdown(f"<div style='text-align: center; font-size: 13px;'>{vendor}</div>", unsafe_allow_html=True)
                
                currency = parsed_json.get('currency', '$')
                if not currency: 
                    currency = '$'
                
                def safe_extract_number(val):
                    if val is None or val == "":
                        return 0.0
                    if isinstance(val, (int, float)):
                        return float(val)
                    clean_str = str(val).replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
                    try:
                        return float(clean_str)
                    except ValueError:
                        return 0.0

                raw_tax = parsed_json.get('tax_amount', parsed_json.get('tax', 0.0))
                tax_val = safe_extract_number(raw_tax)
                tax_display = f"{currency}{tax_val:.2f}"
                r_cols[3].markdown(f"<div style='text-align: center; font-size: 13px;'>{tax_display}</div>", unsafe_allow_html=True)
                
                raw_total = parsed_json.get('total_amount', parsed_json.get('total', 0.0))
                total_val = safe_extract_number(raw_total)
                total_display = f"{currency}{total_val:.2f}"
                r_cols[4].markdown(f"<div style='text-align: center; font-size: 13px;'>{total_display}</div>", unsafe_allow_html=True)
                
                conf_val = row.get('overall_confidence')
                if pd.isna(conf_val) or conf_val is None:
                    conf_display = "N/A"
                else:
                    try:
                        conf_display = f"{float(conf_val)*100:.0f}%"
                    except:
                        conf_display = "N/A"
                r_cols[5].markdown(f"<div style='text-align: center; font-size: 13px;'>{conf_display}</div>", unsafe_allow_html=True)
                
                with r_cols[6]:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("📄", key=f"json_{row['id']}", help="View Extracted JSON"):
                            view_json_dialog(row.get('extracted_json', '{}'))
                    with btn_col2:
                        if st.button("🖼️", key=f"img_{row['id']}", help="View Original Image"):
                            view_photo_dialog(row['id'])
                
                st.markdown("<hr style='margin: 0px; padding: 0px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        prev_col, text_col, next_col = st.columns([1, 2, 1])
        
        with prev_col:
            if st.button("⬅️ Previous", disabled=(st.session_state.db_page == 1), use_container_width=True):
                st.session_state.db_page -= 1
                st.rerun()
                
        with text_col:
            st.markdown(f"<h5 style='text-align: center;'>Page {st.session_state.db_page} of {total_pages}</h5>", unsafe_allow_html=True)
            
        with next_col:
            if st.button("Next ➡️", disabled=(st.session_state.db_page == total_pages), use_container_width=True):
                st.session_state.db_page += 1
                st.rerun()