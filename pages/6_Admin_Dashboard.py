"""
Admin Dashboard Page
System administrator dashboard for analytics, usage monitoring, and configuration
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, ".."))

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="⚙️",
    layout="wide",
)

st.markdown("# ⚙️ Admin Dashboard")
st.markdown("System administration, analytics, and configuration")

st.divider()

# Key System Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Users", 1245, "+45")

with col2:
    st.metric("Active Cases", 892, "+78")

with col3:
    st.metric("System Uptime", "99.8%", "-0.2%")

with col4:
    st.metric("API Response Time", "245ms", "-15ms")

st.divider()

# Tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Analytics", "👥 User Management", "⚙️ System Config", "📈 Usage", "🔧 Maintenance"])

with tab1:
    st.markdown("## Platform Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Case Statistics")
        st.metric("Total Cases", 3456)
        st.metric("Resolved Cases", 2892, "83.7%")
        st.metric("Avg Resolution Time", "2.8 days")
        st.metric("Satisfaction Score", "4.6/5")
    
    with col2:
        st.markdown("### Service Distribution")
        services = {
            "PM-KISAN": 1200,
            "e-Shram": 950,
            "Passport": 850,
            "Ayushman Bharat": 320,
            "DigiPay": 136
        }
        for service, count in services.items():
            percentage = (count / 3456) * 100
            st.write(f"- {service}: {count} ({percentage:.1f}%)")

with tab2:
    st.markdown("## User Management")
    
    user_type = st.selectbox(
        "Filter by User Type",
        ["All Users", "Citizens", "VLE Officers", "Compliance Officers", "Admins"]
    )
    
    st.divider()
    
    # Mock user data
    users_data = [
        {
            "user_id": "USR-001",
            "name": "Rajesh Kumar",
            "role": "Citizen",
            "email": "rajesh@example.com",
            "status": "Active",
            "joined": datetime.now() - timedelta(days=30),
            "cases": 5
        },
        {
            "user_id": "USR-002",
            "name": "Priya Singh",
            "role": "VLE Officer",
            "email": "priya.csc@example.com",
            "status": "Active",
            "joined": datetime.now() - timedelta(days=90),
            "cases": 24
        },
        {
            "user_id": "USR-003",
            "name": "Amit Patel",
            "role": "Compliance Officer",
            "email": "amit.officer@example.com",
            "status": "Active",
            "joined": datetime.now() - timedelta(days=180),
            "cases": 156
        }
    ]
    
    for user in users_data:
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.write(f"👤 **{user['name']}** ({user['user_id']})")
            st.write(f"Email: {user['email']}")
        
        with col2:
            st.write(f"Role: {user['role']}")
            st.write(f"Joined: {user['joined'].strftime('%Y-%m-%d')}")
        
        with col3:
            st.write(f"Status: {user['status']}")
            st.write(f"Cases: {user['cases']}")
            
            if st.button("🔑 Manage", key=f"manage_{user['user_id']}"):
                st.info(f"Managing user {user['user_id']}")

with tab3:
    st.markdown("## System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### API Configuration")
        st.write("- **OpenAI Model:** gpt-4-turbo")
        st.write("- **Cohere Model:** command")
        st.write("- **Embeddings:** BGE-large")
        st.write("- **Vector DB:** ChromaDB")
        
        if st.button("🔄 Update LLM Config"):
            st.success("LLM configuration updated")
    
    with col2:
        st.markdown("### Database Configuration")
        st.write("- **PostgreSQL:** neon-prod")
        st.write("- **Connection Pool:** 10")
        st.write("- **Query Timeout:** 30s")
        st.write("- **Backup:** Daily at 2 AM UTC")
        
        if st.button("💾 Trigger Backup"):
            st.success("Backup initiated")

with tab4:
    st.markdown("## Usage Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Daily Active Users")
        st.metric("Today", 342, "+28")
        st.metric("This Week Avg", 315, "+12")
        st.metric("This Month Avg", 278, "+45")
    
    with col2:
        st.markdown("### API Usage")
        st.metric("Queries Today", 12450, "+2300")
        st.metric("Avg Latency", "245ms")
        st.metric("Error Rate", "0.02%", "-0.01%")
    
    st.divider()
    
    st.markdown("### Most Used Features")
    features = {
        "Service Discovery": 45,
        "Eligibility Check": 32,
        "Document Verification": 28,
        "Grievance Filing": 18,
        "Knowledge Search": 15
    }
    for feature, usage_pct in features.items():
        st.write(f"- {feature}: {usage_pct}%")

with tab5:
    st.markdown("## System Maintenance")
    
    st.markdown("### Active Alerts")
    
    alerts = [
        {
            "level": "⚠️ Warning",
            "message": "Database connection pool at 85% capacity",
            "action": "Monitor and scale if needed"
        },
        {
            "level": "ℹ️ Info",
            "message": "Scheduled maintenance on Sunday 2 AM UTC",
            "action": "1 hour expected downtime"
        }
    ]
    
    for alert in alerts:
        with st.expander(f"{alert['level']}"):
            st.write(alert['message'])
            st.info(f"Action: {alert['action']}")
    
    st.divider()
    
    st.markdown("### Scheduled Tasks")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        tasks = [
            ("Database Backup", "Daily, 2 AM UTC", "✅ Healthy"),
            ("Vector DB Sync", "Every 6 hours", "✅ Healthy"),
            ("Cache Clear", "Daily, 12 AM UTC", "✅ Healthy"),
            ("Log Rotation", "Weekly, Monday 1 AM", "✅ Healthy")
        ]
        
        for task, schedule, status in tasks:
            st.write(f"{status} **{task}** - {schedule}")
    
    with col2:
        if st.button("🔧 Run Maintenance", use_container_width=True):
            st.info("Running maintenance tasks...")
            st.success("All maintenance tasks completed")
