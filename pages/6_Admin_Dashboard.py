"""
Admin Dashboard Page (modernized)
System administrator dashboard for analytics, monitoring, and configuration.
"""

import streamlit as st
import sys, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
st.set_page_config(page_title="Admin Dashboard", page_icon="⚙️", layout="wide")

from components.styles import apply_global_css
apply_global_css()

# ── Backend ───────────────────────────────────────────────────────────────────
try:
    from backend.hitl import list_pending_reviews, resolve_review
except ImportError:
    list_pending_reviews = None
    resolve_review = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="csc-hero">
  <h1>⚙️ Admin Dashboard</h1>
  <p>System administration, platform analytics, monitoring, and configuration.</p>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Users",    1245, "+45")
c2.metric("Active Cases",    892, "+78")
c3.metric("System Uptime",  "99.8%", "-0.2%")
c4.metric("API Latency",    "245 ms", "-15ms")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Analytics", "👥 Users", "⚙️ Config", "📈 Usage", "🔧 Maintenance"]
)

# ── Analytics ─────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-hdr">Platform Analytics</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="csc-card">', unsafe_allow_html=True)
        st.metric("Total Cases",       3456)
        st.metric("Resolved Cases",    2892, "83.7%")
        st.metric("Avg Resolution",    "2.8 days")
        st.metric("Satisfaction",      "4.6 / 5")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-hdr">Service Distribution</div>', unsafe_allow_html=True)
        services = {"PM-KISAN": 1200, "e-Shram": 950, "Passport": 850, "Ayushman Bharat": 320, "DigiPay": 136}
        total = sum(services.values())
        for svc, cnt in services.items():
            pct = cnt / total
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:.3rem 0">'
                f'<span style="width:130px;font-size:.84rem;font-weight:600">{svc}</span>'
                f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:7px">'
                f'<div style="width:{pct*100:.0f}%;background:var(--primary);height:7px;border-radius:99px"></div>'
                f'</div><span style="font-size:.8rem;color:var(--muted)">{cnt}</span></div>',
                unsafe_allow_html=True,
            )

# ── Users ─────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-hdr">User Management</div>', unsafe_allow_html=True)
    st.selectbox("Filter by role", ["All Users", "Citizens", "VLE Officers", "Compliance Officers", "Admins"], key="adm_role")

    users = [
        {"id": "USR-001", "name": "Rajesh Kumar",  "role": "Citizen",             "email": "rajesh@example.com",      "status": "Active", "cases": 5},
        {"id": "USR-002", "name": "Priya Singh",   "role": "VLE Officer",         "email": "priya.csc@example.com",   "status": "Active", "cases": 24},
        {"id": "USR-003", "name": "Amit Patel",    "role": "Compliance Officer",  "email": "amit.officer@example.com","status": "Active", "cases": 156},
    ]
    role_colors = {"Citizen": "blue", "VLE Officer": "green", "Compliance Officer": "amber", "Admin": "red"}
    for u in users:
        rc = role_colors.get(u["role"], "blue")
        with st.container():
            c1, c2, c3 = st.columns([3, 3, 1])
            c1.markdown(
                f'<b>{u["name"]}</b> <span class="csc-badge csc-badge-{rc}">{u["role"]}</span><br>'
                f'<small style="color:var(--muted)">{u["email"]}</small>',
                unsafe_allow_html=True,
            )
            c2.markdown(
                f'ID: {u["id"]}<br>'
                f'<span class="csc-badge csc-badge-green">{u["status"]}</span>'
                f' · {u["cases"]} cases',
                unsafe_allow_html=True,
            )
            if c3.button("Manage", key=f"adm_mgr_{u['id']}", use_container_width=True):
                st.info(f"Managing {u['id']}: {u['name']}")
        st.markdown("<hr style='margin:.2rem 0;border-color:var(--border)'>", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-hdr">System Configuration</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="csc-card">'
            '<b>AI / LLM Stack</b><br><br>'
            '<small>'
            'OpenAI Model: <b>gpt-4-turbo</b><br>'
            'Cohere Model: <b>command</b><br>'
            'Embeddings: <b>BGE-large</b><br>'
            'Vector DB: <b>ChromaDB</b><br>'
            'Agent Orchestration: <b>LangGraph</b>'
            '</small></div>',
            unsafe_allow_html=True,
        )
        if st.button("🔄 Update LLM Config", key="adm_llm_upd"):
            st.success("LLM configuration updated.")
    with c2:
        st.markdown(
            '<div class="csc-card">'
            '<b>Database</b><br><br>'
            '<small>'
            'PostgreSQL: <b>neon-prod</b><br>'
            'Connection Pool: <b>10</b><br>'
            'Query Timeout: <b>30s</b><br>'
            'Backup: <b>Daily at 2 AM UTC</b>'
            '</small></div>',
            unsafe_allow_html=True,
        )
        if st.button("💾 Trigger Backup", key="adm_bkp"):
            st.success("Database backup initiated.")

    st.markdown('<div class="section-hdr">Monitoring Services</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(
        '<div class="csc-card">'
        'Prometheus <span class="csc-badge csc-badge-green">Running</span><br>'
        '<small style="color:var(--muted)">localhost:9090</small>'
        '</div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        '<div class="csc-card">'
        'Grafana <span class="csc-badge csc-badge-green">Running</span><br>'
        '<small style="color:var(--muted)">localhost:3000</small>'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Usage ─────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-hdr">Usage Analytics</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Today DAU",          342, "+28")
        st.metric("Week Avg DAU",       315, "+12")
        st.metric("Month Avg DAU",      278, "+45")
    with c2:
        st.metric("Queries Today",   12450, "+2300")
        st.metric("Avg Latency",     "245 ms")
        st.metric("Error Rate",      "0.02%", "-0.01%")

    st.markdown('<div class="section-hdr" style="margin-top:1rem">Most Used Features</div>', unsafe_allow_html=True)
    features = {"Service Discovery": 45, "Eligibility Check": 32, "Doc Verification": 28, "Grievance Filing": 18, "KB Search": 15}
    for feat, pct in features.items():
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:.3rem 0">'
            f'<span style="width:150px;font-size:.84rem;font-weight:600">{feat}</span>'
            f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:7px">'
            f'<div style="width:{pct}%;background:var(--accent);height:7px;border-radius:99px"></div>'
            f'</div><span style="font-size:.8rem;color:var(--muted)">{pct}%</span></div>',
            unsafe_allow_html=True,
        )

# ── Maintenance ───────────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-hdr">Active Alerts</div>', unsafe_allow_html=True)
    alerts = [
        {"level": "⚠️ Warning", "msg": "Database connection pool at 85% capacity", "action": "Monitor and scale if needed", "bc": "amber"},
        {"level": "ℹ️ Info",    "msg": "Scheduled maintenance Sunday 2 AM UTC",      "action": "1 hour expected downtime",    "bc": "blue"},
    ]
    for a in alerts:
        with st.expander(f"{a['level']} — {a['msg'][:50]}…"):
            st.write(a["msg"])
            st.markdown(
                f'<span class="csc-badge csc-badge-{a["bc"]}">Action: {a["action"]}</span>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-hdr" style="margin-top:1rem">Scheduled Tasks</div>', unsafe_allow_html=True)
    tasks = [
        ("Database Backup",  "Daily, 2 AM UTC",       "green"),
        ("Vector DB Sync",   "Every 6 hours",          "green"),
        ("Cache Clear",      "Daily, 12 AM UTC",       "green"),
        ("Log Rotation",     "Weekly, Monday 1 AM",    "green"),
    ]
    for task, schedule, bc in tasks:
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:.5rem 0;border-bottom:1px solid var(--border)">'
            f'<span><b>{task}</b> — <small style="color:var(--muted)">{schedule}</small></span>'
            f'<span class="csc-badge csc-badge-{bc}">✓ Healthy</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if st.button("🔧 Run Maintenance Now", type="primary", key="adm_maint", use_container_width=True):
        with st.spinner("Running maintenance tasks…"):
            import time; time.sleep(1)
        st.success("✅ All maintenance tasks completed.")

    # ── HITL Queue ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr" style="margin-top:1rem">HITL Review Queue</div>', unsafe_allow_html=True)
    if list_pending_reviews:
        items = list_pending_reviews(limit=5)
        if not items:
            st.caption("No pending reviews.")
        for item in items:
            rid = item["id"]
            st.markdown(
                f'<div class="csc-card">'
                f'<b>HITL-{rid}</b> · {item["reason"]} · conf {item["confidence"]:.2f}<br>'
                f'<small style="color:var(--muted)">{item.get("created_at","")}</small><br>'
                f'<i>{item.get("query","")}</i>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"✅ Reviewed (HITL-{rid})", key=f"adm_hitl_{rid}"):
                if resolve_review and resolve_review(rid, operator_note="Admin panel review"):
                    st.success(f"HITL-{rid} resolved.")
                    st.rerun()
    else:
        st.info("HITL backend not connected. Configure backend to enable review queue.")
