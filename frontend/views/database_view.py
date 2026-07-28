import streamlit as st
import pandas as pd
import json
import math
from frontend.services import api_client
from frontend.components.dialogs import view_photo_dialog, view_json_dialog

def render_database_view():
    st.markdown("### 🗄️ Document Database")
    st.markdown("Review and manage all extracted documents.")
    
    # Initialize session state for pagination
    if 'db_page' not in st.session_state:
        st.session_state.db_page = 1

    # 1. Fetch Data
    raw_data = api_client.fetch_documents()
    if raw_data is None:
        st.error("Failed to connect to backend API.")
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(raw_data)

    if df.empty:
        st.info("No documents found in the database yet.")
        return

    # 2. Pre-process JSON into DataFrame columns for Sorting/Searching
    def parse_json_data(row):
        json_str = row.get('extracted_json', '{}')
        parsed = {}
        if not pd.isna(json_str) and json_str:
            try:
                parsed = json.loads(json_str) if isinstance(json_str, str) else json_str
            except:
                pass
                
        vendor = parsed.get('vendor_name', parsed.get('vendor', 'N/A')) or 'N/A'
        currency = parsed.get('currency', '$') or '$'
        
        def safe_extract(val):
            if val is None or val == "": return 0.0
            if isinstance(val, (int, float)): return float(val)
            try: 
                return float(str(val).replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip())
            except: 
                return 0.0
                
        tax = safe_extract(parsed.get('tax_amount', parsed.get('tax', 0.0)))
        total = safe_extract(parsed.get('total_amount', parsed.get('total', 0.0)))
        
        return pd.Series([vendor, currency, tax, total])

    # Apply the parsing function to create new sortable columns
    df[['parsed_vendor', 'parsed_currency', 'parsed_tax', 'parsed_total']] = df.apply(parse_json_data, axis=1)

    # 3. UI Controls for Search, Filter, Sort
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    
    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Search vendors, files, etc...")
    with col2:
        statuses = ["All"] + df['status'].dropna().unique().tolist()
        selected_status = st.selectbox("🚦 Status", statuses)
    with col3:
        # Define user-friendly column names for sorting
        sort_options = {
            "Created Date": "created_at",
            "Vendor": "parsed_vendor",
            "Total Amount": "parsed_total",
            "Tax Amount": "parsed_tax",
            "Confidence": "overall_confidence"
        }
        sort_choice = st.selectbox("↕️ Sort By", list(sort_options.keys()))
        sort_col = sort_options[sort_choice]
    with col4:
        sort_order = st.radio("Order", ["Desc", "Asc"], horizontal=True)

    # 4. Apply Filters & Sorting
    if search_term:
        mask = df.astype(str).apply(lambda col: col.str.contains(search_term, case=False, na=False)).any(axis=1)
        df = df[mask]

    if selected_status != "All":
        df = df[df['status'] == selected_status]

    # Ensure the sort column exists before sorting
    if sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=(sort_order == "Asc"))

    # 5. Pagination Logic
    ITEMS_PER_PAGE = 10
    total_items = len(df)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1
    
    # Reset page if filtering reduces total pages below current page
    if st.session_state.db_page > total_pages:
        st.session_state.db_page = 1
        
    start_idx = (st.session_state.db_page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_df = df.iloc[start_idx:end_idx]

    # 6. Render the Data Table
    st.markdown(f"**Showing {total_items} results**")
    
    with st.container(border=True):
        # Adjusted the last column ratio from 1.5 to 1.8 to fit 3 buttons nicely
        col_ratios = [2.2, 1.1, 1.8, 0.9, 0.9, 0.9, 1.8]
        h_cols = st.columns(col_ratios)
        headers = ["Filename", "Status", "Vendor Name", "Tax", "Total", "Conf.", "Actions"]
        for i, text in enumerate(headers):
            h_cols[i].markdown(f"**{text}**")
        st.divider()
        
        for index, row in page_df.iterrows():
            r_cols = st.columns(col_ratios, vertical_alignment="center")
            
            # Filename
            fname = row.get('filename', 'Unknown')
            fname = fname[:22] + "..." if len(fname) > 25 else fname
            r_cols[0].markdown(f"{fname}")
            
            # Status
            status = row.get('status', 'pending')
            status_text = "Approved" if status in ['auto_approved', 'approved'] else "Review"
            r_cols[1].markdown(f"{status_text}")
                
            # Pre-parsed data
            vendor = row['parsed_vendor']
            currency = row['parsed_currency']
            tax_val = row['parsed_tax']
            total_val = row['parsed_total']
            
            r_cols[2].markdown(f"{vendor}")
            r_cols[3].markdown(f"{currency}{tax_val:.2f}")
            r_cols[4].markdown(f"{currency}{total_val:.2f}")
            
            # Confidence
            conf_val = row.get('overall_confidence')
            conf_display = f"{float(conf_val)*100:.0f}%" if pd.notna(conf_val) and conf_val is not None else "N/A"
            r_cols[5].markdown(f"{conf_display}")
            
            # Actions (3 Buttons)
            with r_cols[6]:
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if st.button("🤖", key=f"ext_{row['id']}", help="View Extracted JSON"):
                        view_json_dialog(row.get('extracted_json', '{}'))
                with btn_col2:
                    if st.button("🧑‍💻", key=f"rev_{row['id']}", help="View Reviewed JSON"):
                        reviewed_data = row.get('reviewed_json', '')
                        if pd.notna(reviewed_data) and str(reviewed_data).strip() != "":
                            view_json_dialog(reviewed_data)
                        else:
                            st.toast("No reviewed JSON available for this document.")
                with btn_col3:
                    if st.button("🖼️", key=f"img_{row['id']}", help="View Original Image"):
                        view_photo_dialog(row['id'])
            
            st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 1px solid #eee;' />", unsafe_allow_html=True)

    # 7. Pagination Controls
    st.markdown("<br>", unsafe_allow_html=True)
    prev_col, text_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if st.button("⬅️ Previous", disabled=(st.session_state.db_page == 1), use_container_width=True):
            st.session_state.db_page -= 1
            st.rerun()
    with text_col:
        st.markdown(f"<div style='text-align: center;'>Page {st.session_state.db_page} of {total_pages}</div>", unsafe_allow_html=True)
    with next_col:
        if st.button("Next ➡️", disabled=(st.session_state.db_page == total_pages), use_container_width=True):
            st.session_state.db_page += 1
            st.rerun()