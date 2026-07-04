"""
Grievance Redressal Page (modernized)
Complaint management, SLA tracking, and ticket lifecycle.
"""

import streamlit as st
import sys, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="Grievance Redressal", page_icon="📋", layout="wide")

from components.styles import apply_global_css
apply_global_css()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="csc-hero">
  <h1>📋 Grievance Redressal</h1>
  <p>Submit and track complaints with SLA management and real-time status updates.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Metric row ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Complaints",       1245, "+12")
c2.metric("Resolved",                892,  "+8")
c3.metric("Pending",                 353,  "+4")
c4.metric("Avg Resolution Time", "3.2 days", "-0.5")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📝 File Complaint", "📊 My Complaints", "📈 Analytics"])

# ── File Complaint ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-hdr">File a New Complaint</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        complaint_type = st.selectbox(
            "Complaint Type",
            ["Service Quality", "Staff Behavior", "Document Denial", "Service Delay", "Incorrect Information", "Other"],
            key="grv_type",
        )
        department = st.selectbox(
            "Related Department",
            ["CSC Service", "PM-KISAN", "Passport", "e-Shram", "Ayushman Bharat", "DigiPay"],
            key="grv_dept",
        )
    with c2:
        severity = st.selectbox(
            "Severity Level",
            ["Low", "Medium", "High", "Critical"],
            key="grv_severity",
        )
        complaint_date = st.date_input("Incident Date", value=datetime.now(), key="grv_date")

    description = st.text_area(
        "Complaint Description",
        placeholder="Describe your complaint in detail…",
        height=140,
        key="grv_desc",
    )
    uploaded_file = st.file_uploader(
        "Attach supporting documents (PDF, Images)",
        type=["pdf", "jpg", "png", "docx"],
        key="grv_file",
    )

    if st.button("📤 Submit Complaint", type="primary", key="grv_submit"):
        if description:
            ticket = f"CSC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            severity_colors = {"Low": "green", "Medium": "amber", "High": "red", "Critical": "red"}
            bc = severity_colors.get(severity, "blue")
            st.success(f"✅ Complaint submitted successfully!")
            st.markdown(
                f'<div class="csc-card">'
                f'<b>Ticket ID:</b> {ticket} &nbsp;'
                f'<span class="csc-badge csc-badge-{bc}">{severity}</span><br>'
                f'<small style="color:var(--muted)">Expected resolution: 3-5 business days</small>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.error("Please provide a complaint description.")

# ── My Complaints ──────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-hdr">Your Complaints</div>', unsafe_allow_html=True)

    complaints = [
        {
            "id": "CSC-20240620001",
            "status": "In Progress",
            "dept": "PM-KISAN",
            "date": datetime.now() - timedelta(days=5),
            "sla": "2 days remaining",
            "desc": "Incorrect eligibility notification",
        },
        {
            "id": "CSC-20240615002",
            "status": "Resolved",
            "dept": "e-Shram",
            "date": datetime.now() - timedelta(days=10),
            "sla": "Resolved",
            "desc": "Document verification delay",
        },
    ]

    status_colors = {"In Progress": "amber", "Resolved": "green", "Escalated": "red"}

    for comp in complaints:
        sc = status_colors.get(comp["status"], "blue")
        with st.expander(f"🎟️ {comp['id']} — {comp['status']}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    f'<b>Status:</b> <span class="csc-badge csc-badge-{sc}">{comp["status"]}</span><br>'
                    f'<b>Department:</b> {comp["dept"]}<br>'
                    f'<b>Filed:</b> {comp["date"].strftime("%Y-%m-%d")}',
                    unsafe_allow_html=True,
                )
            with c2:
                st.write(f"**SLA:** {comp['sla']}")
                st.write(f"**Description:** {comp['desc']}")
            bc1, bc2, bc3 = st.columns(3)
            if bc1.button("📞 Contact Officer", key=f"contact_{comp['id']}", use_container_width=True):
                st.info("Officer contact: csc-helpdesk@gov.in | 1800-121-3468")
            if bc2.button("📎 Add Update", key=f"update_{comp['id']}", use_container_width=True):
                st.text_input("Your update:", key=f"upd_in_{comp['id']}")
            if bc3.button("📋 Full Details", key=f"details_{comp['id']}", use_container_width=True):
                st.write(f"Full details for {comp['id']}: {comp['desc']}")

# ── Analytics ──────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-hdr">Grievance Analytics</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="csc-card"><b>Complaints by Department</b><br><br>'
            + "".join(
                f'<div style="display:flex;align-items:center;gap:10px;margin:.3rem 0">'
                f'<span style="width:120px;font-size:.85rem;font-weight:600">{dept}</span>'
                f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:7px">'
                f'<div style="width:{pct}%;background:var(--primary);height:7px;border-radius:99px"></div>'
                f'</div><span style="font-size:.83rem;color:var(--muted)">{cnt}</span></div>'
                for dept, cnt, pct in [
                    ("PM-KISAN", 340, 73), ("e-Shram", 280, 60), ("Passport", 250, 54),
                    ("Ayushman", 210, 45), ("DigiPay", 165, 35),
                ]
            )
            + "</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="csc-card"><b>Resolution Status</b><br><br>'
            + "".join(
                f'<div style="display:flex;align-items:center;gap:8px;margin:.4rem 0">'
                f'<span class="csc-badge csc-badge-{bc}">{status}</span>'
                f'<span style="font-size:.85rem">{count} ({pct}%)</span></div>'
                for status, count, pct, bc in [
                    ("Resolved", 892, 72, "green"),
                    ("In Progress", 280, 22, "amber"),
                    ("Escalated", 73, 6, "red"),
                ]
            )
            + "</div>",
            unsafe_allow_html=True,
        )
