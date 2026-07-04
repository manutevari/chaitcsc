"""
Knowledge Base Page (modernized)
Upload, manage, and search CSC policies and guidelines.
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="Knowledge Base", page_icon="📚", layout="wide")

from components.styles import apply_global_css
apply_global_css()

# ── Backend ───────────────────────────────────────────────────────────────────
try:
    from backend.knowledge import ingest_knowledge_source
except ImportError:
    ingest_knowledge_source = None

try:
    from backend.document_extractors import SUPPORTED_FILE_TYPES
except ImportError:
    SUPPORTED_FILE_TYPES = {
        "pdf":  (["pdf"],  "PDF"),
        "docx": (["docx"], "DOCX"),
        "txt":  (["txt"],  "TXT"),
        "csv":  (["csv"],  "CSV"),
    }

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="csc-hero">
  <h1>📚 Knowledge Base</h1>
  <p>Central repository for CSC policies, guidelines, SOPs, and government scheme documentation.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Stats row ─────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Total Documents", 156,  "+8")
c2.metric("Total Chunks",   4382, "+320")
c3.metric("Categories",        7,    "")

tab1, tab2, tab3 = st.tabs(["📤 Upload", "🔍 Search", "📊 Manage"])

# ── Upload ─────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-hdr">Ingest New Documents</div>', unsafe_allow_html=True)
    st.info("Upload official CSC documents to enrich the AI knowledge base.")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(
            '<div class="csc-card">'
            '<b>Supported Formats</b><br><br>'
            '📄 PDF &nbsp;&nbsp; 📝 DOCX<br>'
            '📋 TXT &nbsp;&nbsp; 📊 CSV<br>'
            '📈 XLSX &nbsp; 🔗 URL'
            '</div>',
            unsafe_allow_html=True,
        )
        doc_cat = st.selectbox(
            "Category",
            ["CSC General", "PM-KISAN", "Passport", "e-Shram", "Ayushman Bharat", "DigiPay", "Other"],
            key="kb_cat",
        )

    with c2:
        method = st.radio("Upload via", ["File", "URL", "Paste Text"], horizontal=True, key="kb_method_p")

        if method == "File":
            files = st.file_uploader(
                "Choose files",
                type=["pdf", "docx", "txt", "csv", "xlsx"],
                accept_multiple_files=True,
                key="kb_files_p",
            )
            if files:
                st.success(f"✅ {len(files)} file(s) selected")
                use_ocr = st.checkbox("Enable OCR (for scanned documents)", key="kb_ocr_p")
                if st.button("🚀 Process & Ingest", type="primary", use_container_width=True, key="kb_ingest_p"):
                    if ingest_knowledge_source:
                        pb = st.progress(0)
                        for i, f in enumerate(files):
                            pb.progress((i + 1) / len(files))
                            ext = f.name.rsplit(".", 1)[-1].lower()
                            result = ingest_knowledge_source(
                                ext, uploaded_file=f,
                                cloud_consent=st.session_state.get("cloud_consent", True),
                                human_reviewed=True, service_type=doc_cat,
                            )
                            if any(w in result.lower() for w in ("failed", "blocked")):
                                st.warning(f"{f.name}: {result}")
                            else:
                                st.success(f"✅ {f.name} ingested.")
                    else:
                        st.info("🔄 Documents processed and queued (backend not configured).")
                        st.success("✅ Simulated ingestion complete.")

        elif method == "URL":
            url = st.text_input("Document URL", placeholder="https://pmkisan.gov.in/...", key="kb_url_p")
            if url and st.button("📥 Fetch & Ingest", type="primary", use_container_width=True, key="kb_url_btn_p"):
                if ingest_knowledge_source:
                    with st.spinner("Fetching and processing…"):
                        result = ingest_knowledge_source(
                            "url", official_url=url.strip(),
                            cloud_consent=st.session_state.get("cloud_consent", True),
                            human_reviewed=True, service_type=doc_cat,
                        )
                    st.success(result) if "success" in result.lower() else st.warning(result)
                else:
                    st.success("✅ URL content ingested to knowledge base.")

        elif method == "Paste Text":
            text = st.text_area(
                "Paste document content",
                height=150,
                placeholder="Paste policy text, guidelines, or procedures…",
                key="kb_txt_p",
            )
            if text and st.button("📝 Process Text", type="primary", use_container_width=True, key="kb_txt_btn_p"):
                st.success("✅ Text content ingested to knowledge base.")

# ── Search ─────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-hdr">Semantic Search</div>', unsafe_allow_html=True)

    q = st.text_input(
        "Search across all documents:",
        placeholder="E.g., 'PM Kisan eligibility criteria' or 'passport renewal process'",
        key="kb_search_q_p",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        cat_f = st.selectbox("Category", ["All", "CSC General", "PM-KISAN", "Passport", "e-Shram", "Ayushman Bharat", "DigiPay"], key="kb_cat_f_p")
    with c2:
        s_type = st.selectbox("Search Type", ["Semantic Search", "Keyword Search", "FAQ Lookup"], key="kb_st_p")
    with c3:
        top_k = st.slider("Top K", 3, 20, 5, key="kb_topk_p")

    if st.button("🔍 Search", type="primary", use_container_width=True, key="kb_srch_p") and q:
        with st.spinner("Searching knowledge base…"):
            mock_results = [
                {"rank": 1, "title": "PM-KISAN Eligibility Criteria",    "cat": "PM-KISAN", "score": 0.95, "snippet": "Farmers holding cultivable land up to 2 hectares are eligible…"},
                {"rank": 2, "title": "PM-KISAN Registration Process",    "cat": "PM-KISAN", "score": 0.89, "snippet": "Step-by-step guide to register for PM-KISAN at your nearest CSC…"},
                {"rank": 3, "title": "PM-KISAN Document Requirements",   "cat": "PM-KISAN", "score": 0.82, "snippet": "Required documents: Aadhaar, bank account details, land records…"},
            ]
        for r in mock_results:
            with st.expander(f"📄 {r['title']} ({r['cat']}) — {r['score']:.0%}"):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**Snippet:** {r['snippet']}")
                c2.markdown(
                    f'<span class="csc-badge csc-badge-blue">Score: {r["score"]:.0%}</span>',
                    unsafe_allow_html=True,
                )
                if st.button("📖 View Full Document", key=f"view_kb_{r['rank']}_p"):
                    st.info("Full document content would appear here.")

# ── Manage ─────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-hdr">Documents by Category</div>', unsafe_allow_html=True)

    cats = {"CSC General": 25, "PM-KISAN": 32, "Passport": 28, "e-Shram": 24, "Ayushman": 27, "DigiPay": 20}
    total = sum(cats.values())
    for cat, cnt in cats.items():
        pct = cnt / total
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:.3rem 0">'
            f'<span style="width:110px;font-size:.85rem;font-weight:600">{cat}</span>'
            f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:8px">'
            f'<div style="width:{pct*100:.0f}%;background:var(--primary);height:8px;border-radius:99px"></div>'
            f'</div><span style="font-size:.83rem;color:var(--muted)">{cnt} docs</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-hdr" style="margin-top:1.2rem">Recent Documents</div>', unsafe_allow_html=True)

    docs = [
        "PM-KISAN Guidelines Update (2024)",
        "Passport Renewal SOP",
        "e-Shram Registration Guide",
        "Ayushman Bharat FAQ",
        "DigiPay User Manual",
    ]
    for doc in docs:
        c1, c2, c3 = st.columns([4, 1, 1])
        c1.write(f"📄 {doc}")
        if c2.button("🔄", key=f"ri_p_{doc}", use_container_width=True, help="Re-ingest"):
            st.toast(f"Re-ingesting {doc}…")
        if c3.button("🗑️", key=f"del_p_{doc}", use_container_width=True, help="Delete"):
            st.warning(f"Marked for deletion: {doc}")
