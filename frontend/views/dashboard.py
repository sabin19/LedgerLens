import streamlit as st
import pandas as pd
import json
from datetime import datetime
from frontend.services import api_client

def render_dashboard():
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown("### 📈 Executive Dashboard")
        st.markdown("Overview of processed documents, total spend, and automation performance.")
    with header_col2:
        if st.button("🚀 Process Document", type="primary", use_container_width=True):
            st.session_state.switch_to_upload = True
            st.rerun()
    
    raw_data = api_client.fetch_documents()
    if raw_data is None:
        st.error("Failed to connect to backend API.")
        dashboard_df = pd.DataFrame()
    else:
        dashboard_df = pd.DataFrame(raw_data)

    if dashboard_df.empty:
        st.info("Upload your first document to populate the dashboard!")
        if st.button("🚀 Process Your First Document", type="primary"):
            st.session_state.switch_to_upload = True
            st.rerun()
        return

    # --- Data Safeties & Assumptions ---
    # Ensure a status column exists
    if 'status' not in dashboard_df.columns:
        dashboard_df['status'] = 'unknown'
        
    # Ensure a date column exists for "Today's Uploads" and "Daily Chart"
    # Adjust 'uploaded_at' to match your actual database column name (e.g., 'created_at')
    if 'uploaded_at' not in dashboard_df.columns:
        dashboard_df['uploaded_at'] = pd.Timestamp.now()
    
    # Convert dates to datetime objects
    dashboard_df['uploaded_at'] = pd.to_datetime(dashboard_df['uploaded_at'], errors='coerce')

    totals = []
    vendors = []
    confidences = []
    
    for _, row in dashboard_df.iterrows():
        reviewed_raw = row.get('reviewed_json')
        json_str = reviewed_raw if (pd.notna(reviewed_raw) and str(reviewed_raw).strip() != '') else row.get('extracted_json', '{}')
        try:
            data = json.loads(json_str) if isinstance(json_str, str) else json_str
            if not isinstance(data, dict):
                data = {}
        except:
            data = {}
        
        # 1. Parse Total
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
        
        # 2. Parse Vendor
        v = data.get('vendor_name', data.get('vendor', 'Unknown'))
        vendors.append(v if v else "Unknown")
        
        # 3. Parse AI Confidence (Checks inside extracted_json first, then row level)
        conf = data.get('confidence', row.get('confidence', 0.0))
        try:
            c = float(conf)
        except (ValueError, TypeError):
            c = 0.0
        confidences.append(c)
        
    dashboard_df['parsed_total'] = totals
    dashboard_df['parsed_vendor'] = vendors
    dashboard_df['parsed_confidence'] = confidences
    
    # --- Metrics Calculations ---
    total_docs = len(dashboard_df)
    
    # Depending on your business logic, "Uploaded" might mean documents still waiting in the queue. 
    # If "Uploaded" means strictly total documents ever added, you can set it to `total_docs`.
    uploaded_docs = len(dashboard_df[dashboard_df['status'].isin(['uploaded', 'pending', 'received'])])
    
    processed_docs = len(dashboard_df[~dashboard_df['status'].isin(['uploaded', 'pending', 'received'])])
    approved_docs = len(dashboard_df[dashboard_df['status'].isin(['auto_approved', 'approved'])])
    
    today = pd.Timestamp.today().normalize()
    todays_uploads = len(dashboard_df[dashboard_df['uploaded_at'].dt.normalize() == today])
    
    avg_confidence = dashboard_df['parsed_confidence'].mean() if not dashboard_df['parsed_confidence'].empty else 0.0
    total_spend = sum(totals)
    
    approval_rate = (approved_docs / processed_docs) * 100 if processed_docs > 0 else 0.0
    
    # --- Render Metrics (Grid Layout) ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 1
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        with st.container(border=True):
            st.metric(label="Total Documents", value=f"{total_docs}")
    with m2:
        with st.container(border=True):
            st.metric(label="Uploaded (Pending)", value=f"{uploaded_docs}")
    with m3:
        with st.container(border=True):
            st.metric(label="Processed Documents", value=f"{processed_docs}")
    with m4:
        with st.container(border=True):
            st.metric(label="Approved Documents", value=f"{approved_docs}")

    # Row 2
    st.markdown("<br>", unsafe_allow_html=True)
    m5, m6, m7, m8 = st.columns(4)
    with m5:
        with st.container(border=True):
            st.metric(label="Today's Uploads", value=f"{todays_uploads}")
    with m6:
        with st.container(border=True):
            # Formats gracefully whether backend sends confidence as 0.95 or 95.0
            conf_display = f"{avg_confidence:.1f}%" if avg_confidence > 1 else f"{avg_confidence * 100:.1f}%"
            st.metric(label="Avg AI Confidence", value=conf_display)
    with m7:
        with st.container(border=True):
            st.metric(label="Total Spend Processed", value=f"{total_spend:,.2f}")
    with m8:
        with st.container(border=True):
            st.metric(label="STP / Approval Rate", value=f"{approval_rate:.1f}%")

    # --- Render Charts ---
    st.markdown("<br>", unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns(2, gap="large")
    
    with chart_col1:
        st.markdown("#### 📅 Daily Upload Chart")
        with st.container(border=True):
            # Group by date to get daily upload counts
            daily_uploads = dashboard_df.groupby(dashboard_df['uploaded_at'].dt.date).size()
            if not daily_uploads.empty:
                st.line_chart(daily_uploads, color="#fbbf24")
            else:
                st.write("Not enough data.")
                
    with chart_col2:
        st.markdown("#### 🚦 Status Distribution Chart")
        with st.container(border=True):
            status_counts = dashboard_df['status'].value_counts()
            if not status_counts.empty:
                st.bar_chart(status_counts, color="#60a5fa")
            else:
                st.write("Not enough data.")

    # Retained the Vendor chart in a full-width bottom section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🏆 Top Vendors by Spend")
    with st.container(border=True):
        vendor_spend = dashboard_df.groupby('parsed_vendor')['parsed_total'].sum().sort_values(ascending=False).head(5)
        if not vendor_spend.empty:
            st.bar_chart(vendor_spend, color="#4ade80")
        else:
            st.write("Not enough data.")