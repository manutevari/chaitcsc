"""
CSC Mitra AI – Global CSS Design System
All visual tokens, glassmorphism, animations, and typography in one place.
Import and call apply_global_css() once per page to activate.
"""

import streamlit as st


# ── Design tokens ─────────────────────────────────────────────────────────────
_GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');

:root {
  --primary:       #005bac;
  --primary-light: #e0f0ff;
  --accent:        #ff6b00;
  --success:       #16a34a;
  --warning:       #d97706;
  --danger:        #dc2626;
  --ink:           #0f172a;
  --muted:         #64748b;
  --surface:       #ffffff;
  --bg:            #f1f5f9;
  --border:        #e2e8f0;
  --radius:        12px;
  --shadow-sm:     0 1px 3px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.06);
  --shadow-md:     0 4px 16px rgba(15,23,42,.10), 0 2px 6px rgba(15,23,42,.06);
  --shadow-lg:     0 10px 30px rgba(15,23,42,.12), 0 4px 10px rgba(15,23,42,.08);
}

/* ── Base ──────────────────────────────────────────────────────────────────── */
html, body,
[class*="css"],
.stMarkdown, .stTextInput, .stTextArea,
.stButton, .stSelectbox, .stRadio {
  font-family: Inter, "Noto Sans Devanagari", "Nirmala UI", system-ui, sans-serif !important;
}

.stApp { background: var(--bg); color: var(--ink); }

.block-container {
  max-width: 980px;
  padding-top: 1.5rem;
  padding-bottom: 3.5rem;
}

/* ── Sidebar ───────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox > div,
[data-testid="stSidebar"] .stCheckbox { border-color: #334155 !important; }

/* ── Navigation tabs ───────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px;
  font-weight: 600;
  font-size: .93rem;
  padding: 8px 18px;
  transition: background .15s, color .15s;
}
.stTabs [aria-selected="true"] {
  background: var(--primary) !important;
  color: #ffffff !important;
}

/* ── Cards ─────────────────────────────────────────────────────────────────── */
.csc-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 1.25rem 1.4rem;
  margin-bottom: 1rem;
  transition: box-shadow .2s;
}
.csc-card:hover { box-shadow: var(--shadow-md); }
.csc-card-glass {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  padding: 1.25rem 1.4rem;
  margin-bottom: 1rem;
}

/* ── Hero banner ───────────────────────────────────────────────────────────── */
.csc-hero {
  background: linear-gradient(135deg, #005bac 0%, #0284c7 50%, #0891b2 100%);
  border-radius: var(--radius);
  padding: 1.6rem 1.8rem;
  margin-bottom: 1.2rem;
  position: relative;
  overflow: hidden;
}
.csc-hero::after {
  content: '';
  position: absolute;
  top: -40%; right: -10%;
  width: 320px; height: 320px;
  background: rgba(255,255,255,.07);
  border-radius: 50%;
}
.csc-hero h1 { color: #fff; font-size: 1.7rem; font-weight: 800; margin: 0 0 6px; }
.csc-hero p  { color: rgba(255,255,255,.87); font-size: .97rem; margin: 0; }

/* ── Greeting / empty state ────────────────────────────────────────────────── */
.csc-greeting {
  text-align: center;
  padding: 2.5rem 1rem;
  color: var(--muted);
}
.csc-greeting h2 { font-size: 1.45rem; font-weight: 700; color: var(--ink); margin-bottom: .4rem; }
.csc-greeting p  { font-size: 1rem; }

/* ── Quick prompt chips ─────────────────────────────────────────────────────── */
.prompt-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: .6rem 0 1.2rem;
  justify-content: center;
}
.prompt-chip {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: .85rem;
  font-weight: 500;
  padding: 6px 14px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}
.prompt-chip:hover {
  border-color: var(--primary);
  background: var(--primary-light);
  color: var(--primary);
}

/* ── Chat messages ──────────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  margin-bottom: .75rem;
  padding: .9rem 1.1rem;
}
[data-testid="stChatMessage"][data-testid*="user"] {
  background: var(--primary-light);
  border-color: #bfdbfe;
}
[data-testid="stChatMessageContent"] { line-height: 1.7; }

/* ── Input area ─────────────────────────────────────────────────────────────── */
textarea {
  border-radius: 10px !important;
  border-color: var(--border) !important;
  font-size: 1rem !important;
}
textarea:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(0,91,172,.14) !important; }

/* ── Buttons ────────────────────────────────────────────────────────────────── */
.stButton > button {
  border-radius: 9px;
  font-weight: 600;
  min-height: 40px;
  transition: transform .12s, box-shadow .12s;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: var(--shadow-md); }
.stButton > button[kind="primary"] { background: var(--primary); border-color: var(--primary); }
.stButton > button[kind="primary"]:hover { background: #004a8c; border-color: #004a8c; }

/* ── Metric cards ────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  box-shadow: var(--shadow-sm);
}
[data-testid="stMetricLabel"]  { font-size: .83rem; font-weight: 600; color: var(--muted); }
[data-testid="stMetricValue"]  { font-size: 1.7rem; font-weight: 800; color: var(--ink);   }
[data-testid="stMetricDelta"]  { font-size: .82rem; font-weight: 600; }

/* ── Status badges ───────────────────────────────────────────────────────────── */
.csc-badge {
  display: inline-flex; align-items: center; gap: 5px;
  border-radius: 999px; font-size: .78rem; font-weight: 700;
  padding: 3px 10px; white-space: nowrap;
}
.csc-badge-green  { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.csc-badge-blue   { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
.csc-badge-amber  { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
.csc-badge-red    { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

/* ── Pulse dot animation ─────────────────────────────────────────────────────── */
.pulse-dot {
  display: inline-block; width: 8px; height: 8px;
  border-radius: 50%; background: var(--success);
  animation: pulse-anim 1.4s ease-in-out infinite;
}
@keyframes pulse-anim {
  0%, 100% { opacity: .3; transform: scale(.8); }
  50%       { opacity: 1;  transform: scale(1.1); }
}

/* ── Section header ──────────────────────────────────────────────────────────── */
.section-hdr {
  font-size: 1rem; font-weight: 800; color: var(--ink);
  border-left: 3px solid var(--primary); padding-left: 10px;
  margin: 1.4rem 0 .8rem;
}

/* ── Responsive ──────────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .block-container { padding-left: .9rem; padding-right: .9rem; }
  .csc-hero h1 { font-size: 1.3rem; }
  .stTabs [data-baseweb="tab"] { padding: 6px 12px; font-size: .85rem; }
}
"""


def apply_global_css() -> None:
    """Inject the shared design system CSS. Call once at the top of any page."""
    st.markdown(f"<style>{_GLOBAL_CSS}</style>", unsafe_allow_html=True)


def card(content_html: str, cls: str = "csc-card") -> None:
    """Render wrapped content inside a styled card div."""
    st.markdown(f'<div class="{cls}">{content_html}</div>', unsafe_allow_html=True)


def badge(label: str, color: str = "blue") -> str:
    """Return an HTML badge string for inline use."""
    return f'<span class="csc-badge csc-badge-{color}">{label}</span>'
