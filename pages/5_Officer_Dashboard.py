"""
Officer Dashboard Page (modernized)
Compliance officer case assignment and SLA management.
"""

import streamlit as st
import sys, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
st.set_page_config(page_title="Officer Dashboard", page_icon="👮", layout="wide")

from components.styles import apply_global_css
apply_global_css()

st.markdown(
    """
<div class="csc-hero">
  <h1>👮 Officer Dashboard</h1>
  <p>Compliance officer case assignment, SLA tracking, and escalation management.</p>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Assigned Cases",  42, "+5")
c2.metric("SLA Alerts",       8, "+2")
c3.metric("Escalations",      3, "-1")
c4.metric("Compliance Rate", "94.2%", "+2.1%")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Assigned Cases", "⚠️ SLA Alerts", "📈 Escalations", "📊 Analytics"])

_PCOLOR = {"Critical": "red", "High": "red", "Medium": "amber", "Low": "green"}

_CASES = [
    {"id": "CSC-2024-0521", "vle": "Rajesh CSC Center", "service": "PM-KISAN",  "priority": "High",     "status": "In Review",          "sla_h": 6},
    {"id": "CSC-2024-0520", "vle": "Priya CSC Center",  "service": "e-Shram",   "priority": "Medium",   "status": "Pending Verification","sla_h": 18},
    {"id": "CSC-2024-0519", "vle": "Amit CSC Center",   "service": "Passport",  "priority": "Low",      "status": "Completed",           "sla_h": 0},
]

with tab1:
    st.markdown('<div class="section-hdr">Assigned Cases</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    c1.text_input("Search", placeholder="Case ID or VLE name", key="off_search")
    c2.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"], key="off_pf")

    for case in _CASES:
        pc = _PCOLOR.get(case["priority"], "blue")
        sla_bc = "red" if case["sla_h"] <= 6 else "amber" if case["sla_h"] <= 12 else "green"
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.markdown(
                f'<b>{case["id"]}</b><br>'
                f'<span style="font-size:.82rem;color:var(--muted)">{case["vle"]}</span>',
                unsafe_allow_html=True,
            )
            c2.markdown(
                f'📋 {case["service"]}<br>'
                f'<span class="csc-badge csc-badge-{pc}">{case["priority"]}</span>',
                unsafe_allow_html=True,
            )
            c3.markdown(
                f'{case["status"]}<br>'
                f'<span class="csc-badge csc-badge-{sla_bc}">'
                f'{"✓ Done" if case["sla_h"]==0 else f"{case[\"sla_h\"]}h left"}'
                f'</span>',
                unsafe_allow_html=True,
            )
            if c4.button("✅ Approve", key=f"off_app_{case['id']}", use_container_width=True):
                st.success(f"Approved {case['id']}")
            if c4.button("📝 Review", key=f"off_rev_{case['id']}", use_container_width=True):
                st.info(f"Reviewing {case['id']}")
        st.markdown("<hr style='margin:.2rem 0;border-color:var(--border)'>", unsafe_allow_html=True)

_ALERTS = [
    {"id": "CSC-2024-0521", "service": "PM-KISAN",  "alert": "Critical – 6 h left",  "vle": "Rajesh CSC"},
    {"id": "CSC-2024-0518", "service": "e-Shram",   "alert": "Warning – 4 h left",   "vle": "Amit CSC"},
    {"id": "CSC-2024-0517", "service": "Passport",  "alert": "Critical – 2 h left",  "vle": "Priya CSC"},
]

with tab2:
    st.markdown('<div class="section-hdr">SLA Alerts</div>', unsafe_allow_html=True)
    for a in _ALERTS:
        is_crit = "Critical" in a["alert"]
        with st.expander(f"{'🔴' if is_crit else '🟡'} {a['id']} — {a['alert']}"):
            c1, c2 = st.columns(2)
            c1.markdown(f'<b>Service:</b> {a["service"]}<br><b>VLE:</b> {a["vle"]}', unsafe_allow_html=True)
            if c2.button("⚡ Escalate",     key=f"off_esc_{a['id']}", use_container_width=True):
                st.warning(f"Escalated {a['id']}")
            if c2.button("⏱️ Extend SLA", key=f"off_ext_{a['id']}", use_container_width=True):
                st.success(f"SLA extended for {a['id']}")

_ESCS = [
    {"id": "CSC-2024-0516", "reason": "Compliance violation",       "severity": "High",     "when": "1d ago"},
    {"id": "CSC-2024-0515", "reason": "Document authenticity issue","severity": "Critical",  "when": "6h ago"},
    {"id": "CSC-2024-0514", "reason": "Eligibility dispute",        "severity": "Medium",   "when": "12h ago"},
]

with tab3:
    st.markdown('<div class="section-hdr">Escalations</div>', unsafe_allow_html=True)
    for e in _ESCS:
        sc = _PCOLOR.get(e["severity"], "blue")
        with st.expander(f"{'🔴' if e['severity']=='Critical' else '🟠'} {e['id']} — {e['reason']}"):
            c1, c2 = st.columns(2)
            c1.markdown(
                f'<span class="csc-badge csc-badge-{sc}">{e["severity"]}</span><br>'
                f'<small style="color:var(--muted)">Escalated: {e["when"]}</small>',
                unsafe_allow_html=True,
            )
            if c2.button("✅ Resolve", key=f"off_res_esc_{e['id']}", use_container_width=True):
                st.success(f"Resolved {e['id']}")

with tab4:
    st.markdown('<div class="section-hdr">Performance Analytics</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Cases Reviewed", 156)
    c2.metric("Approval Rate",  "92.3%")
    c3.metric("Avg Review Time","1.2 days")

    st.markdown('<div class="section-hdr" style="margin-top:1rem">Case Distribution</div>', unsafe_allow_html=True)
    dist = {"PM-KISAN": 45, "e-Shram": 35, "Passport": 40, "Ayushman": 25, "DigiPay": 11}
    total = sum(dist.values())
    for svc, cnt in dist.items():
        pct = cnt / total * 100
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:.3rem 0">'
            f'<span style="width:100px;font-size:.85rem;font-weight:600">{svc}</span>'
            f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:7px">'
            f'<div style="width:{pct:.0f}%;background:var(--primary);height:7px;border-radius:99px"></div>'
            f'</div><span style="font-size:.83rem;color:var(--muted)">{cnt}</span></div>',
            unsafe_allow_html=True,
        )
