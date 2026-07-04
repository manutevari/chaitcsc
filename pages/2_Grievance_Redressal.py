"""
Grievance Redressal Page
Complaint management, SLA tracking, and ticket lifecycle
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, ".."))

st.set_page_config(
    page_title="Grievance Redressal",
    page_icon="❌",
    layout="wide",
)

st.markdown("# ❌ Grievance Redressal")
st.markdown("Submit and track complaints with SLA management")

st.divider()

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📝 File Complaint", "📊 My Complaints", "📈 Analytics"])

with tab1:
    st.markdown("## File a New Complaint")
    
    col1, col2 = st.columns(2)
    
    with col1:
        complaint_type = st.selectbox(
            "Complaint Type",
            ["Service Quality", "Staff Behavior", "Document Denial", 
             "Service Delay", "Incorrect Information", "Other"]
        )
        
        department = st.selectbox(
            "Related Department",
            ["CSC Service", "PM-KISAN", "Passport", 
             "e-Shram", "Ayushman Bharat", "DigiPay"]
        )
    
    with col2:
        severity = st.selectbox(
            "Severity Level",
            ["Low", "Medium", "High", "Critical"]
        )
        
        complaint_date = st.date_input(
            "Incident Date",
            value=datetime.now()
        )
    
    # Complaint description
    description = st.text_area(
        "Complaint Description",
        placeholder="Describe your complaint in detail...",
        height=150
    )
    
    # File attachments
    uploaded_file = st.file_uploader(
        "Attach supporting documents (PDF, Images)",
        type=["pdf", "jpg", "png", "docx"]
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("📤 Submit Complaint", use_container_width=True):
            if description:
                st.success(f"✅ Complaint submitted successfully!")
                st.info(f"📋 Ticket ID: CSC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
                # TODO: Integrate with Grievance Agent and Ticket Engine
            else:
                st.error("Please provide a complaint description")

with tab2:
    st.markdown("## Your Complaints")
    
    # Mock complaint data
    complaints_data = [
        {
            "ticket_id": "CSC-20240620001",
            "status": "In Progress",
            "department": "PM-KISAN",
            "filed_date": datetime.now() - timedelta(days=5),
            "sla_remaining": "2 days",
            "description": "Incorrect eligibility notification"
        },
        {
            "ticket_id": "CSC-20240615002",
            "status": "Resolved",
            "department": "e-Shram",
            "filed_date": datetime.now() - timedelta(days=10),
            "sla_remaining": "Resolved",
            "description": "Document verification delay"
        }
    ]
    
    for complaint in complaints_data:
        with st.expander(f"🎟️ {complaint['ticket_id']} - {complaint['status']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Status:** {complaint['status']}")
                st.write(f"**Department:** {complaint['department']}")
                st.write(f"**Filed Date:** {complaint['filed_date'].strftime('%Y-%m-%d')}")
            
            with col2:
                st.write(f"**SLA Remaining:** {complaint['sla_remaining']}")
                st.write(f"**Description:** {complaint['description']}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📞 Contact Officer", key=f"contact_{complaint['ticket_id']}"):
                    st.info("Officer contact information would appear here")
            with col2:
                if st.button("📎 Add Update", key=f"update_{complaint['ticket_id']}"):
                    st.success("Update section would appear here")
            with col3:
                if st.button("📋 View Details", key=f"details_{complaint['ticket_id']}"):
                    st.write(f"Full details for {complaint['ticket_id']}")

with tab3:
    st.markdown("## Grievance Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Complaints", 1245, "+12")
    with col2:
        st.metric("Resolved", 892, "+8")
    with col3:
        st.metric("Pending", 353, "+4")
    with col4:
        st.metric("Avg Resolution Time", "3.2 days", "-0.5")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Complaints by Department")
        st.markdown("""
        - PM-KISAN: 340
        - e-Shram: 280
        - Passport: 250
        - Ayushman: 210
        - DigiPay: 165
        """)
    
    with col2:
        st.markdown("### Complaints by Status")
        st.markdown("""
        - Resolved: 892 (72%)
        - In Progress: 280 (22%)
        - Escalated: 73 (6%)
        """)
