import streamlit as st
import pandas as pd
import json
import math
from frontend.services import api_client
from frontend.components.dialogs import view_photo_dialog, view_json_dialog

def render_database_view():
    st.markdown("### 🗄️ Document Database")
    st.markdown("Review and manage all extracted documents.")
    
    raw_data = api_client.fetch_documents()
    if raw_data is None:
        st.error("Failed to connect to backend API.")
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(raw_data)

    if df.empty:
        st.info("No documents found in the database yet.")
        return

    ITEMS_PER_PAGE = 10
    total_items = len(df)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    
    if st.session_state.db_page > total_pages:
        st.session_state.db_page = total_pages
        
    start_idx = (st.session_state.db_page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_df = df.iloc[start_idx:end_idx]

    with st.container(border=True):
        col_ratios = [2.2, 1.1, 1.8, 0.9, 0.9, 1.1, 1.5]
        h_cols = st.columns(col_ratios)
        headers = ["Filename", "Status", "Vendor Name", "Tax", "Total", "Conf.", "Actions"]
        for i, text in enumerate(headers):
            h_cols[i].markdown(f"{text}", unsafe_allow_html=True)
        st.divider()
        
        for index, row in page_df.iterrows():
            r_cols = st.columns(col_ratios, vertical_alignment="center")
            
            fname = row.get('filename', 'Unknown')
            fname = fname[:22] + "..." if len(fname) > 25 else fname
            r_cols[0].markdown(f"{fname}", unsafe_allow_html=True)
            
            status = row.get('status', 'pending')
            status_color = "#4ade80" if status == 'auto_approved' else "#facc15"
            status_text = "Approved" if status == 'auto_approved' else "Review"
            r_cols[1].markdown(f"{status_text}", unsafe_allow_html=True)
                
            json_str = row.get('extracted_json', '{}')
            parsed_json = {}
            if not pd.isna(json_str) and json_str:
                try: parsed_json = json.loads(json_str)
                except: pass

            vendor = parsed_json.get('vendor_name', parsed_json.get('vendor', 'N/A')) or 'N/A'
            r_cols[2].markdown(f"{vendor}", unsafe_allow_html=True)
            
            currency = parsed_json.get('currency', '$') or '$'
            
            def safe_extract(val):
                if val is None or val == "": return 0.0
                if isinstance(val, (int, float)): return float(val)
                try: return float(str(val).replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip())
                except: return 0.0

            tax_val = safe_extract(parsed_json.get('tax_amount', parsed_json.get('tax', 0.0)))
            r_cols[3].markdown(f"{currency}{tax_val:.2f}", unsafe_allow_html=True)
            
            total_val = safe_extract(parsed_json.get('total_amount', parsed_json.get('total', 0.0)))
            r_cols[4].markdown(f"{currency}{total_val:.2f}", unsafe_allow_html=True)
            
            conf_val = row.get('overall_confidence')
            conf_display = f"{float(conf_val)*100:.0f}%" if pd.notna(conf_val) and conf_val is not None else "N/A"
            r_cols[5].markdown(f"{conf_display}", unsafe_allow_html=True)
            
            with r_cols[6]:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("📄", key=f"json_{row['id']}", help="View JSON"):
                        view_json_dialog(row.get('extracted_json', '{}'))
                with btn_col2:
                    if st.button("🖼️", key=f"img_{row['id']}", help="View Image"):
                        view_photo_dialog(row['id'])
            
            st.markdown("", unsafe_allow_html=True)

    st.markdown("", unsafe_allow_html=True)
    prev_col, text_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if st.button("⬅️ Previous", disabled=(st.session_state.db_page == 1), use_container_width=True):
            st.session_state.db_page -= 1
            st.rerun()
    with text_col:
        st.markdown(f"Page {st.session_state.db_page} of {total_pages}", unsafe_allow_html=True)
    with next_col:
        if st.button("Next ➡️", disabled=(st.session_state.db_page == total_pages), use_container_width=True):
            st.session_state.db_page += 1
            st.rerun()