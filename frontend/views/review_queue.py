import streamlit as st
import json
from frontend.services import api_client

def render_review_queue():
    st.header("Human Review Queue")
    
    queue = api_client.fetch_review_queue()
    
    if queue is None:
        st.error("Failed to connect to backend. Is the FastAPI server running?")
        return
        
    if not queue:
        st.info("All caught up! No documents pending review.")
        return
        
    for doc in queue:
        with st.expander(f"Pending: {doc['filename']} (ID: {doc['id']})", expanded=True):
            extracted_data = json.loads(doc['extracted_json'])
            st.write("Correct any inaccurate fields below:")
            edited_data = st.data_editor(extracted_data, key=f"editor_{doc['id']}", use_container_width=True)
            
            if st.button("Approve Corrections", key=f"btn_{doc['id']}"):
                status = api_client.approve_document(doc['id'], edited_data)
                if status == 200:
                    st.success("Document approved and committed to storage!")
                    st.rerun()
                else:
                    st.error("Failed to approve document.")