"""
VLE Dashboard Page (modernized)
Village Level Entrepreneur case and service management.
"""

import streamlit as st
import sys, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
st.set_page_config(page_title="VLE Dashboard", page_icon="👤", layout="wide")

from components.styles import apply_global_css
apply_global_css()

st.markdown(
    """
<div class="csc-hero">
  <h1>👤 VLE Dashboard</h1>
  <p>Village Level Entrepreneur — case management, grievances, and performance tracking.</p>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
c1.metric("Active Cases",       24, "+3")
c2.metric("Pending Grievances",  7, "-1")
c3.metric("Service Requests",   12, "+5")

tab1, tab2, tab3, tab4 = st.tabs(["📋 My Cases", "❌ Grievances", "📞 Service Requests", "📊 Performance"])

_PRIORITY_COLOR = {"High": "red", "Medium": "amber", "Low": "green", "Critical": "red"}
_CASES = [
    {"id": "CSC-2024-0521", "citizen": "Rajesh Kumar", "service": "PM-KISAN",  "status": "In Progress",    "priority": "High",   "time": "2h ago"},
    {"id": "CSC-2024-0520", "citizen": "Priya Singh",  "service": "e-Shram",   "status": "Pending Review", "priority": "Medium", "time": "5h ago"},
    {"id": "CSC-2024-0519", "citizen": "Amit Patel",   "service": "Passport",  "status": "Open",           "priority": "Low",    "time": "12h ago"},
]
_GRIEVANCES = [
    {"id": "GRV-2024-003", "type": "Service Delay",    "by": "Rajesh Kumar", "severity": "High",   "days": 3},
    {"id": "GRV-2024-002", "type": "Document Denial",  "by": "Priya Singh",  "severity": "Medium", "days": 1},
]

with tab1:
    st.markdown('<div class="section-hdr">Active Cases</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    c1.text_input("Search", placeholder="Case ID or citizen name", key="vle_search")
    c2.selectbox("Filter", ["All", "Open", "In Progress", "Pending Review", "Closed"], key="vle_filter")

    for case in _CASES:
        pc = _PRIORITY_COLOR.get(case["priority"], "blue")
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.markdown(
                f'<b>{case["id"]}</b><br>'
                f'<span style="font-size:.82rem;color:var(--muted)">👤 {case["citizen"]}</span>',
                unsafe_allow_html=True,
            )
            c2.markdown(
                f'📋 {case["service"]}<br>'
                f'<span style="font-size:.82rem;color:var(--muted)">{case["time"]}</span>',
                unsafe_allow_html=True,
            )
            c3.markdown(
                f'{case["status"]}<br>'
                f'<span class="csc-badge csc-badge-{pc}">{case["priority"]}</span>',
                unsafe_allow_html=True,
            )
            if c4.button("Open", key=f"vle_open_{case['id']}", use_container_width=True):
                st.info(f"Opening {case['id']}")
        st.markdown("<hr style='margin:.2rem 0;border-color:var(--border)'>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-hdr">Pending Grievances</div>', unsafe_allow_html=True)
    for grv in _GRIEVANCES:
        sc = _PRIORITY_COLOR.get(grv["severity"], "blue")
        with st.expander(f"❌ {grv['id']} — {grv['type']} ({grv['severity']})"):
            c1, c2 = st.columns(2)
            c1.markdown(
                f'<b>Filed by:</b> {grv["by"]}<br>'
                f'<b>Pending:</b> {grv["days"]} day(s)<br>'
                f'<span class="csc-badge csc-badge-{sc}">{grv["severity"]}</span>',
                unsafe_allow_html=True,
            )
            if c2.button("✅ Resolve", key=f"vle_res_{grv['id']}", use_container_width=True):
                st.success(f"Marked {grv['id']} as resolved.")
            if c2.button("📝 Add Note", key=f"vle_note_{grv['id']}", use_container_width=True):
                st.text_input("Note:", key=f"vle_note_in_{grv['id']}")

with tab3:
    st.markdown('<div class="section-hdr">Service Requests</div>', unsafe_allow_html=True)
    services = [
        ("PM-KISAN Registration", 5, "amber"),
        ("e-Shram Enrollment",    3, "blue"),
        ("Passport Services",     2, "blue"),
        ("Ayushman Registration", 2, "blue"),
    ]
    for svc, cnt, bc in services:
        c1, c2 = st.columns([4, 1])
        c1.markdown(
            f'<div style="padding:.5rem 0;border-bottom:1px solid var(--border)">'
            f'📋 <b>{svc}</b></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<span class="csc-badge csc-badge-{bc}">{cnt} pending</span>',
            unsafe_allow_html=True,
        )

with tab4:
    st.markdown('<div class="section-hdr">Performance Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Cases Handled",    24)
    c2.metric("Avg Resolution",   "2.5 days")
    c3.metric("Satisfaction",     "4.7/5")

    st.markdown('<div class="section-hdr" style="margin-top:1rem">Service Distribution</div>', unsafe_allow_html=True)
    dist = {"PM-KISAN": 30, "e-Shram": 25, "Passport": 20, "Ayushman": 15, "DigiPay": 10}
    for svc, pct in dist.items():
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:.3rem 0">'
            f'<span style="width:100px;font-size:.85rem;font-weight:600">{svc}</span>'
            f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:7px">'
            f'<div style="width:{pct}%;background:var(--primary);height:7px;border-radius:99px"></div>'
            f'</div><span style="font-size:.83rem;color:var(--muted)">{pct}%</span></div>',
            unsafe_allow_html=True,
        )
