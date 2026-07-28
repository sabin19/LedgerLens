import streamlit as st

# Import our modular views
from frontend.views.dashboard import render_dashboard
from frontend.views.ingestion import render_ingestion
from frontend.views.review_queue import render_review_queue
from frontend.views.database_view import render_database_view

# Configure the global page settings
st.set_page_config(layout="wide", page_title="Invoice Lense")

# Initialize global session state variables
if "doc_image" not in st.session_state:
    st.session_state.doc_image = None
if "db_page" not in st.session_state:
    st.session_state.db_page = 1
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"

# Render main title
st.title("Invoice Lense Document Intelligence")

# Setup Navigation
tabs = ["Dashboard", "Upload Document", "Review Queue", "Database View"]

# Keep active_tab in sync
current_index = tabs.index(st.session_state.active_tab) if st.session_state.active_tab in tabs else 0

selected_tab = st.radio(
    "Navigation",
    tabs,
    index=current_index,
    horizontal=True,
    label_visibility="collapsed",
    key="nav_radio"
)

if selected_tab != st.session_state.active_tab:
    st.session_state.active_tab = selected_tab

if st.session_state.active_tab == "Dashboard":
    render_dashboard()
elif st.session_state.active_tab == "Upload Document":
    render_ingestion()
elif st.session_state.active_tab == "Review Queue":
    render_review_queue()
elif st.session_state.active_tab == "Database View":
    render_database_view()