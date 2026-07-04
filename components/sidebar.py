"""
CSC Mitra AI – Sidebar Component
Dark-themed sidebar with navigation status, session info, and quick settings.
"""

import streamlit as st


_NAV_ITEMS = [
    ("💬", "Assistant", "Chat with CSC Mitra"),
    ("📚", "Knowledge", "Upload & search documents"),
    ("📊", "Dashboard", "Analytics & monitoring"),
    ("⚙️", "Settings",  "Preferences & developer tools"),
]


def render_sidebar() -> dict:
    """
    Render the unified sidebar and return a dict of user settings.
    Keys: cloud_consent, response_language, voice_mode, tts_voice_choice.
    """
    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────────────────────
        st.markdown(
            """
<div style="padding:1rem 0 .5rem;border-bottom:1px solid #334155;margin-bottom:1rem">
  <div style="font-size:1.3rem;font-weight:800;letter-spacing:-.3px">🤝 CSC Mitra AI</div>
  <div style="font-size:.78rem;color:#94a3b8;margin-top:2px">
    Intelligent Citizen Assistant
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ── Connection status ───────────────────────────────────────────────────
        backend_ok = st.session_state.get("backend_available", True)
        dot_color  = "#22c55e" if backend_ok else "#ef4444"
        label      = "Connected" if backend_ok else "Backend Offline"
        st.markdown(
            f"""
<div style="display:flex;align-items:center;gap:8px;background:#1e293b;
            border:1px solid #334155;border-radius:8px;padding:8px 12px;
            margin-bottom:1rem;font-size:.82rem;font-weight:600;color:#e2e8f0">
  <span style="width:8px;height:8px;border-radius:50%;background:{dot_color};
               display:inline-block;animation:pulse-anim 1.4s infinite"></span>
  {label}
</div>
""",
            unsafe_allow_html=True,
        )

        # ── Navigation hint ─────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:.72rem;font-weight:700;color:#64748b;'
            'letter-spacing:.06em;text-transform:uppercase;margin-bottom:.5rem">'
            "Navigation</div>",
            unsafe_allow_html=True,
        )
        for icon, name, desc in _NAV_ITEMS:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;padding:6px 4px;'
                f'border-radius:6px;font-size:.87rem;color:#cbd5e1">'
                f'<span style="font-size:1rem">{icon}</span>'
                f'<span style="font-weight:600">{name}</span>'
                f'<span style="color:#475569;font-size:.78rem">— {desc}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div style="border-top:1px solid #334155;margin:1rem 0"></div>',
            unsafe_allow_html=True,
        )

        # ── Settings ────────────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:.72rem;font-weight:700;color:#64748b;'
            'letter-spacing:.06em;text-transform:uppercase;margin-bottom:.5rem">'
            "Settings</div>",
            unsafe_allow_html=True,
        )

        cloud_consent = st.checkbox(
            "☁️ Cloud processing",
            value=st.session_state.get("cloud_consent", True),
            help="Enable cloud-based AI for better answers.",
            key="cloud_consent",
        )

        response_language = st.selectbox(
            "🌐 Language",
            ["Auto", "English", "Hindi"],
            index=["Auto", "English", "Hindi"].index(
                st.session_state.get("response_language", "Auto")
            ),
            key="response_language",
        )

        voice_mode = st.checkbox(
            "🔊 Auto-play voice",
            key="voice_mode",
            help="Speak answers aloud automatically.",
        )

        tts_voice = st.selectbox(
            "🎙️ Voice style",
            ["Bhashini (default)", "OpenAI Nova", "Gemini-like (neural)", "Microsoft Copilot (neural)"],
            index=["Bhashini (default)", "OpenAI Nova", "Gemini-like (neural)", "Microsoft Copilot (neural)"].index(
                st.session_state.get("tts_voice_choice", "Bhashini (default)")
            ),
            key="tts_voice_choice",
        )

        st.markdown(
            '<div style="border-top:1px solid #334155;margin:1rem 0"></div>',
            unsafe_allow_html=True,
        )

        # ── Session quick stats ─────────────────────────────────────────────────
        msg_count  = len(st.session_state.get("messages", []))
        user_turns = sum(1 for m in st.session_state.get("messages", []) if m.get("role") == "user")
        st.markdown(
            f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:8px;
            padding:10px 12px;font-size:.8rem;color:#94a3b8">
  <div style="font-weight:700;color:#e2e8f0;margin-bottom:6px">📈 Session</div>
  <div>Messages: <b style="color:#e2e8f0">{msg_count}</b></div>
  <div>Your queries: <b style="color:#e2e8f0">{user_turns}</b></div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ── Footer ──────────────────────────────────────────────────────────────
        st.markdown(
            '<div style="position:absolute;bottom:1rem;left:0;right:0;'
            'text-align:center;font-size:.72rem;color:#475569">'
            "CSC Mitra AI © 2024 | Multi-Agent LangGraph</div>",
            unsafe_allow_html=True,
        )

    return {
        "cloud_consent":     cloud_consent,
        "response_language": response_language,
        "voice_mode":        voice_mode,
        "tts_voice_choice":  tts_voice,
    }
