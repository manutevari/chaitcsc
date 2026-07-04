"""
CSC Mitra AI – Header Component
Top-of-page hero banner with branding and status indicator.
"""

import streamlit as st


def render_header(title: str = "CSC Mitra AI", subtitle: str | None = None) -> None:
    """Render the page hero banner."""
    subtitle = subtitle or (
        "Namaste 👋 — Ask about CSC services and government schemes "
        "in Hindi, English, or any Indian language."
    )
    backend_ok = st.session_state.get("backend_available", True)
    status_html = (
        '<span class="csc-badge csc-badge-green"><span class="pulse-dot"></span> Connected</span>'
        if backend_ok else
        '<span class="csc-badge csc-badge-red">⚠ Backend Offline</span>'
    )
    st.markdown(
        f"""
<div class="csc-hero">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.6rem">
    <div>
      <h1 style="margin:0 0 4px">{title}</h1>
      <p style="color:rgba(255,255,255,.85);margin:0;font-size:.95rem">{subtitle}</p>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
      {status_html}
      <span style="font-size:.72rem;color:rgba(255,255,255,.55)">
        DPDP Compliant · Official Sources Only
      </span>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
