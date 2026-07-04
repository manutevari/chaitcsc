"""
Officer Dashboard Page
Compliance officer dashboard for case assignment and SLA management
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, ".."))

st.set_page_config(
    page_title="Officer Dashboard",
    page_icon="👮",
    layout="wide",
)

st.markdown("# 👮 Officer Dashboard")
st.markdown("Compliance officer case assignment and SLA management")

st.divider()

# Key Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Assigned Cases", 42, "+5")

with col2:
    st.metric("SLA Alerts", 8, "+2")

with col3:
    st.metric("Escalations", 3, "-1")

with col4:
    st.metric("Compliance Rate", "94.2%", "+2.1%")

st.divider()

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["📋 Assigned Cases", "⚠️ SLA Alerts", "📈 Escalations", "📊 Analytics"])

with tab1:
    st.markdown("## Assigned Cases")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        search_filter = st.text_input("Search cases:", placeholder="Case ID or VLE name")
    with col2:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "Critical", "High", "Medium", "Low"]
        )
    
    st.divider()
    
    # Mock assigned cases
    assigned_cases = [
        {
            "case_id": "CSC-2024-0521",
            "vle_name": "Rajesh CSC Center",
            "service": "PM-KISAN",
            "priority": "High",
            "status": "In Review",
            "assigned_date": datetime.now() - timedelta(days=2),
            "sla_hours_left": 6
        },
        {
            "case_id": "CSC-2024-0520",
            "vle_name": "Priya CSC Center",
            "service": "e-Shram",
            "priority": "Medium",
            "status": "Pending Verification",
            "assigned_date": datetime.now() - timedelta(days=1),
            "sla_hours_left": 18
        },
        {
            "case_id": "CSC-2024-0519",
            "vle_name": "Amit CSC Center",
            "service": "Passport",
            "priority": "Low",
            "status": "Completed",
            "assigned_date": datetime.now() - timedelta(days=3),
            "sla_hours_left": 0
        }
    ]
    
    for case in assigned_cases:
        # Color code by priority
        priority_color = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢"
        }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write(f"🎟️ **{case['case_id']}**")
            st.write(f"CSC: {case['vle_name']}")
        
        with col2:
            st.write(f"📋 {case['service']}")
            st.write(f"{priority_color.get(case['priority'], '⚪')} {case['priority']}")
        
        with col3:
            st.write(f"Status: {case['status']}")
            sla_color = "🟢" if case['sla_hours_left'] > 12 else "🟡" if case['sla_hours_left'] > 6 else "🔴"
            st.write(f"{sla_color} SLA: {case['sla_hours_left']}h left")
        
        with col4:
            if st.button("✅ Approve", key=f"approve_{case['case_id']}", use_container_width=True):
                st.success(f"Approved {case['case_id']}")
            if st.button("📝 Review", key=f"review_{case['case_id']}", use_container_width=True):
                st.info(f"Opening review for {case['case_id']}")

with tab2:
    st.markdown("## SLA Alerts")
    
    sla_alerts = [
        {
            "case_id": "CSC-2024-0521",
            "service": "PM-KISAN",
            "alert_type": "Critical - 6 hours left",
            "vle": "Rajesh CSC Center"
        },
        {
            "case_id": "CSC-2024-0518",
            "service": "e-Shram",
            "alert_type": "Warning - 4 hours left",
            "vle": "Amit CSC Center"
        },
        {
            "case_id": "CSC-2024-0517",
            "service": "Passport",
            "alert_type": "Critical - 2 hours left",
            "vle": "Priya CSC Center"
        }
    ]
    
    for alert in sla_alerts:
        alert_emoji = "🔴" if "Critical" in alert['alert_type'] else "🟡"
        
        with st.expander(f"{alert_emoji} {alert['case_id']} - {alert['alert_type']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Service:** {alert['service']}")
                st.write(f"**VLE:** {alert['vle']}")
            
            with col2:
                if st.button("⚡ Escalate", key=f"escalate_{alert['case_id']}"):
                    st.warning(f"Escalated {alert['case_id']}")
                if st.button("⏱️ Extend SLA", key=f"extend_{alert['case_id']}"):
                    st.success(f"SLA extended for {alert['case_id']}")

with tab3:
    st.markdown("## Escalations")
    
    escalations = [
        {
            "case_id": "CSC-2024-0516",
            "reason": "Compliance violation",
            "severity": "High",
            "escalated_date": datetime.now() - timedelta(days=1)
        },
        {
            "case_id": "CSC-2024-0515",
            "reason": "Document authenticity issue",
            "severity": "Critical",
            "escalated_date": datetime.now() - timedelta(hours=6)
        },
        {
            "case_id": "CSC-2024-0514",
            "reason": "Eligibility dispute",
            "severity": "Medium",
            "escalated_date": datetime.now() - timedelta(hours=12)
        }
    ]
    
    for esc in escalations:
        severity_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡"}.get(esc['severity'], "🟢")
        
        with st.expander(f"{severity_emoji} {esc['case_id']} - {esc['reason']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Severity:** {esc['severity']}")
                st.write(f"**Escalated:** {esc['escalated_date'].strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                if st.button("✅ Resolve", key=f"resolve_esc_{esc['case_id']}"):
                    st.success(f"Marked {esc['case_id']} as resolved")

with tab4:
    st.markdown("## Officer Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### This Month")
        st.metric("Cases Reviewed", 156)
        st.metric("Approval Rate", "92.3%")
        st.metric("Avg Review Time", "1.2 days")
    
    with col2:
        st.markdown("### Case Distribution")
        dist = {
            "PM-KISAN": 45,
            "e-Shram": 35,
            "Passport": 40,
            "Ayushman": 25,
            "DigiPay": 11
        }
        for service, count in dist.items():
            st.write(f"- {service}: {count} cases")
