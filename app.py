"""
CSC Mitra AI - Home Page
Multi-agent platform for Citizen Service Centre (CSC) governance
"""

import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set page config
st.set_page_config(
    page_title="CSC Mitra AI - Home",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .feature-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        font-size: 0.95rem;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# Logo and Title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div class="main-header">
        <h1>🤝 CSC Mitra AI</h1>
        <p style="font-size: 1.1rem; color: #666;">
            Intelligent Assistant for Citizen Service Centers
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Welcome Section
st.markdown("""
## Welcome to CSC Mitra

CSC Mitra AI is an intelligent, multi-agent platform designed to revolutionize how Citizen Service Centres deliver services. 
Using cutting-edge AI, natural language processing, and knowledge management, CSC Mitra assists:

- **Citizens** with service discovery, eligibility checks, and grievance redressal
- **VLE Officers** with workflow guidance and document verification
- **Compliance Officers** with policy compliance checks
- **Administrators** with analytics and system management
""")

st.divider()

# Key Features
st.markdown("## 🚀 Key Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🔍 Service Discovery
    Find the right CSC service based on your needs
    
    ### 📋 Eligibility Assessment
    Check if you qualify for specific government schemes
    
    ### 📄 Document Verification
    AI-powered verification of required documents
    """)

with col2:
    st.markdown("""
    ### 💬 Grievance Redressal
    Submit and track service complaints with SLA management
    
    ### 📚 Knowledge Base
    Comprehensive repository of CSC policies and guidelines
    
    ### 📊 Analytics Dashboard
    Real-time insights into services and performance
    """)

st.divider()

# Navigation to Pages
st.markdown("## 📱 Navigate to:")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    if st.button("🤖 CSC Assistant", use_container_width=True, key="nav_assistant"):
        st.switch_page("pages/1_CSC_Assistant.py")
    if st.button("❌ Grievance Redressal", use_container_width=True, key="nav_grievance"):
        st.switch_page("pages/2_Grievance_Redressal.py")

with nav_col2:
    if st.button("📚 Knowledge Base", use_container_width=True, key="nav_kb"):
        st.switch_page("pages/3_Knowledge_Base.py")
    if st.button("👤 VLE Dashboard", use_container_width=True, key="nav_vle"):
        st.switch_page("pages/4_VLE_Dashboard.py")

with nav_col3:
    if st.button("👮 Officer Dashboard", use_container_width=True, key="nav_officer"):
        st.switch_page("pages/5_Officer_Dashboard.py")
    if st.button("⚙️ Admin Dashboard", use_container_width=True, key="nav_admin"):
        st.switch_page("pages/6_Admin_Dashboard.py")

st.divider()

# Architecture Overview
st.markdown("## 🏗️ Architecture")

st.markdown("""
**CSC Mitra** operates on a sophisticated multi-agent architecture:

- **Intent Agent**: Understands user queries and determines intent
- **Service Discovery Agent**: Identifies relevant government services
- **Eligibility Agent**: Assesses user eligibility for schemes
- **Document Verification Agent**: Validates required documents
- **Compliance Agent**: Ensures policy compliance
- **Grievance Agent**: Manages complaint lifecycle
- **Workflow Guidance Agent**: Provides step-by-step assistance
- **Fusion Agent**: Orchestrates all agents for complex queries

All agents are powered by:
- 🧠 **LangGraph** for agent orchestration
- 🔍 **ChromaDB** for knowledge retrieval
- 💾 **PostgreSQL** for data persistence
- 🤖 **LLMs** (OpenAI, Cohere) for intelligence
""")

st.divider()

# Footer
st.markdown("""
<div style="text-align: center; color: #999; margin-top: 2rem;">
    <p>CSC Mitra AI © 2024 | Powered by Multi-Agent LangGraph Architecture</p>
    <p>
        <a href="#" style="color: #667eea; text-decoration: none;">Documentation</a> • 
        <a href="#" style="color: #667eea; text-decoration: none;">Support</a> • 
        <a href="#" style="color: #667eea; text-decoration: none;">Privacy</a>
    </p>
</div>
""", unsafe_allow_html=True)
