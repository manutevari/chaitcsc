"""
VLE Dashboard Page
Village Level Entrepreneur dashboard for case and service management
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, ".."))

st.set_page_config(
    page_title="VLE Dashboard",
    page_icon="👤",
    layout="wide",
)

st.markdown("# 👤 VLE Dashboard")
st.markdown("Village Level Entrepreneur case and service management")

st.divider()

# VLE Profile Section
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Active Cases", 24, "+3")

with col2:
    st.metric("Pending Grievances", 7, "-1")

with col3:
    st.metric("Service Requests", 12, "+5")

st.divider()

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["📋 My Cases", "❌ Grievances", "📞 Service Requests", "📊 Performance"])

with tab1:
    st.markdown("## Active Cases")
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_case = st.text_input("Search cases:", placeholder="Case ID or citizen name")
    with col2:
        case_filter = st.selectbox(
            "Filter by Status",
            ["All", "Open", "In Progress", "Pending Review", "Closed"]
        )
    
    st.divider()
    
    # Mock cases data
    cases_data = [
        {
            "case_id": "CSC-2024-0521",
            "citizen_name": "Rajesh Kumar",
            "service": "PM-KISAN",
            "status": "In Progress",
            "last_update": datetime.now() - timedelta(hours=2),
            "priority": "High"
        },
        {
            "case_id": "CSC-2024-0520",
            "citizen_name": "Priya Singh",
            "service": "e-Shram",
            "status": "Pending Review",
            "last_update": datetime.now() - timedelta(hours=5),
            "priority": "Medium"
        },
        {
            "case_id": "CSC-2024-0519",
            "citizen_name": "Amit Patel",
            "service": "Passport",
            "status": "Open",
            "last_update": datetime.now() - timedelta(hours=12),
            "priority": "Low"
        }
    ]
    
    for case in cases_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write(f"🎟️ **{case['case_id']}**")
            st.write(f"👤 {case['citizen_name']}")
        
        with col2:
            st.write(f"📋 {case['service']}")
            st.write(f"🔴 {case['priority']}")
        
        with col3:
            status_emoji = "✅" if case['status'] == "Closed" else "⏳"
            st.write(f"{status_emoji} {case['status']}")
            st.write(f"🕒 {case['last_update'].strftime('%H:%M')}")
        
        with col4:
            if st.button("📂 Open", key=f"open_{case['case_id']}", use_container_width=True):
                st.info(f"Opening case {case['case_id']}")
            if st.button("✏️ Edit", key=f"edit_{case['case_id']}", use_container_width=True):
                st.info(f"Editing case {case['case_id']}")

with tab2:
    st.markdown("## Pending Grievances")
    
    grievances = [
        {
            "ticket_id": "GRV-2024-003",
            "type": "Service Delay",
            "filed_by": "Rajesh Kumar",
            "severity": "High",
            "days_pending": 3
        },
        {
            "ticket_id": "GRV-2024-002",
            "type": "Document Denial",
            "filed_by": "Priya Singh",
            "severity": "Medium",
            "days_pending": 1
        }
    ]
    
    for grv in grievances:
        with st.expander(f"❌ {grv['ticket_id']} - {grv['type']} ({grv['severity']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Filed by:** {grv['filed_by']}")
                st.write(f"**Pending for:** {grv['days_pending']} days")
            
            with col2:
                if st.button("📞 Resolve", key=f"resolve_{grv['ticket_id']}"):
                    st.success(f"Marked {grv['ticket_id']} as resolved")
                if st.button("📝 Add Note", key=f"note_{grv['ticket_id']}"):
                    st.text_input("Add resolution note:", key=f"note_input_{grv['ticket_id']}")

with tab3:
    st.markdown("## Service Requests")
    
    services = [
        ("PM-KISAN Registration", 5),
        ("e-Shram Enrollment", 3),
        ("Passport Services", 2),
        ("Ayushman Registration", 2)
    ]
    
    for service, count in services:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"📋 {service}")
        with col2:
            st.metric("Pending", count)

with tab4:
    st.markdown("## Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### This Month")
        st.metric("Cases Handled", 24)
        st.metric("Avg Resolution Time", "2.5 days")
        st.metric("Satisfaction Score", "4.7/5")
    
    with col2:
        st.markdown("### Service Distribution")
        services_dist = {
            "PM-KISAN": 30,
            "e-Shram": 25,
            "Passport": 20,
            "Ayushman": 15,
            "DigiPay": 10
        }
        for service, pct in services_dist.items():
            st.write(f"- {service}: {pct}%")
