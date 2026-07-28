import streamlit as st

# Import our modular views
from frontend.views.dashboard import render_dashboard
from frontend.views.ingestion import render_ingestion
from frontend.views.review_queue import render_review_queue
from frontend.views.database_view import render_database_view

# Configure the global page settings
st.set_page_config(layout="wide", page_title="LedgerLens")

# Initialize global session state variables
if "doc_image" not in st.session_state:
    st.session_state.doc_image = None
if "db_page" not in st.session_state:
    st.session_state.db_page = 1

# Render main title
st.title("LedgerLens Document Intelligence")

# Setup Navigation
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Upload Document", "Review Queue", "Database View"])

with tab1:
    render_dashboard()

with tab2:
    render_ingestion()

with tab3:
    render_review_queue()

with tab4:
    render_database_view()