import streamlit as st
import streamlit.components.v1 as components

# Import our modular views and auth service
from frontend.services.auth import get_required_access_token, verify_token
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
if "switch_to_upload" not in st.session_state:
    st.session_state.switch_to_upload = False
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Render main title
st.title("Invoice Lense Document Intelligence")

# Check Token Authentication Gate
required_token = get_required_access_token()
if required_token and not st.session_state.authenticated:
    st.warning("🔒 Access Restricted: Please enter your access token to continue.")
    with st.form("token_auth_form", clear_on_submit=False):
        user_token = st.text_input("Access Token", type="password", help="Enter the secret access token configured in environment variables.")
        submit = st.form_submit_button("Access Dashboard")
        if submit:
            if verify_token(user_token):
                st.session_state.authenticated = True
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("Invalid Access Token. Access Denied.")
    st.stop()

# Sidebar Logout Option (when authenticated)
if required_token and st.session_state.authenticated:
    with st.sidebar:
        if st.button("🔒 Lock / Logout"):
            st.session_state.authenticated = False
            st.rerun()

# Setup Navigation using native Streamlit Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Upload Document", "Review Queue", "Database View"])

with tab1:
    render_dashboard()

with tab2:
    render_ingestion()

with tab3:
    render_review_queue()

with tab4:
    render_database_view()

# Programmatic tab switcher triggered from Dashboard button click
if st.session_state.get("switch_to_upload"):
    st.session_state.switch_to_upload = False
    components.html(
        """
        <script>
            setTimeout(function() {
                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"], [role="tab"]');
                if (tabs && tabs.length > 1) {
                    tabs[1].click();
                }
            }, 100);
        </script>
        """,
        height=0,
    )