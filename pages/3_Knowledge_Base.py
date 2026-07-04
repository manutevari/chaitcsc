"""
Knowledge Base Page
Upload, manage, and search CSC policies and guidelines
"""

import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, ".."))

st.set_page_config(
    page_title="Knowledge Base",
    page_icon="📚",
    layout="wide",
)

st.markdown("# 📚 Knowledge Base")
st.markdown("Central repository for CSC policies, guidelines, and procedures")

st.divider()

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "🔍 Search", "📊 Manage"])

with tab1:
    st.markdown("## Upload Documents")
    st.info("Upload CSC policies, guidelines, SOPs, and educational materials")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Supported Formats:")
        st.markdown("""
        - 📄 PDF
        - 📊 DOCX
        - 📋 TXT
        - 🔗 URLs
        """)
        
        document_category = st.selectbox(
            "Document Category",
            ["CSC General", "PM-KISAN", "Passport", 
             "e-Shram", "Ayushman Bharat", "DigiPay", "Other"]
        )
    
    with col2:
        st.markdown("### Upload Options:")
        
        upload_method = st.radio(
            "Choose upload method:",
            ["File Upload", "URL", "Paste Text"]
        )
        
        if upload_method == "File Upload":
            uploaded_files = st.file_uploader(
                "Choose files to upload",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                st.info(f"🎯 {len(uploaded_files)} file(s) ready for upload")
                
                # Processing options
                st.markdown("### Processing Options:")
                chunk_strategy = st.selectbox(
                    "Chunking Strategy",
                    ["Semantic Chunks", "Fixed Size (1000 tokens)", "By Section"]
                )
                
                use_ocr = st.checkbox("Enable OCR for scanned documents", value=False)
                
                if st.button("🚀 Process & Ingest", use_container_width=True):
                    st.info("🔄 Processing documents...")
                    st.success("✅ Documents processed and ingested to ChromaDB")
                    # TODO: Integrate with ingestion.py service
        
        elif upload_method == "URL":
            url_input = st.text_input("Enter document URL:")
            if url_input and st.button("📥 Fetch & Ingest from URL", use_container_width=True):
                st.info("🔄 Fetching and processing URL content...")
                st.success("✅ Content ingested to knowledge base")
        
        elif upload_method == "Paste Text":
            text_input = st.text_area(
                "Paste document content:",
                height=150,
                placeholder="Paste policy text, guidelines, or procedures..."
            )
            if text_input and st.button("📝 Process Text", use_container_width=True):
                st.success("✅ Text content ingested to knowledge base")

with tab2:
    st.markdown("## Search Knowledge Base")
    
    # Search interface
    search_query = st.text_input(
        "Search across all documents:",
        placeholder="E.g., 'PM Kisan eligibility criteria' or 'passport renewal process'"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_category = st.selectbox(
            "Filter by Category",
            ["All", "CSC General", "PM-KISAN", "Passport", 
             "e-Shram", "Ayushman Bharat", "DigiPay"]
        )
    
    with col2:
        search_type = st.selectbox(
            "Search Type",
            ["Semantic Search", "Keyword Search", "FAQ Lookup"]
        )
    
    with col3:
        top_k = st.slider("Top K Results", 3, 20, 5)
    
    if st.button("🔍 Search", use_container_width=True):
        if search_query:
            st.info(f"Searching for: '{search_query}'")
            
            # Mock search results
            search_results = [
                {
                    "rank": 1,
                    "title": "PM-KISAN Eligibility Criteria",
                    "category": "PM-KISAN",
                    "relevance": 0.95,
                    "snippet": "Farmers holding cultivable land up to 2 hectares are eligible for PM-KISAN scheme..."
                },
                {
                    "rank": 2,
                    "title": "PM-KISAN Registration Process",
                    "category": "PM-KISAN",
                    "relevance": 0.89,
                    "snippet": "Step-by-step guide to register for PM-KISAN at your nearest CSC..."
                },
                {
                    "rank": 3,
                    "title": "PM-KISAN Document Requirements",
                    "category": "PM-KISAN",
                    "relevance": 0.82,
                    "snippet": "Required documents include Aadhaar, bank account details, land records..."
                }
            ]
            
            st.divider()
            for result in search_results:
                with st.expander(
                    f"📄 {result['title']} ({result['category']}) - "
                    f"Relevance: {result['relevance']:.0%}"
                ):
                    st.write(f"**Category:** {result['category']}")
                    st.write(f"**Relevance Score:** {result['relevance']:.0%}")
                    st.write(f"**Snippet:** {result['snippet']}")
                    
                    if st.button("📖 View Full Document", key=f"view_{result['rank']}"):
                        st.info("Full document content would appear here")
        else:
            st.warning("Please enter a search query")

with tab3:
    st.markdown("## Manage Knowledge Base")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Knowledge Base Statistics")
        st.metric("Total Documents", 156)
        st.metric("Total Chunks", 4382)
        st.metric("Last Updated", "2024-06-20")
    
    with col2:
        st.markdown("### Documents by Category")
        categories = {
            "CSC General": 25,
            "PM-KISAN": 32,
            "Passport": 28,
            "e-Shram": 24,
            "Ayushman": 27,
            "DigiPay": 20
        }
        for cat, count in categories.items():
            st.write(f"- {cat}: {count} documents")
    
    st.divider()
    
    st.markdown("### Recent Documents")
    recent_docs = [
        "PM-KISAN Guidelines Update (2024)",
        "Passport Renewal SOP",
        "e-Shram Registration Guide",
        "Ayushman Bharat FAQ",
        "DigiPay User Manual"
    ]
    
    for doc in recent_docs:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"📄 {doc}")
        with col2:
            if st.button("🔄 Re-ingest", key=f"reingest_{doc}"):
                st.success(f"Re-ingesting {doc}...")
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{doc}"):
                st.warning(f"Marked {doc} for deletion")
