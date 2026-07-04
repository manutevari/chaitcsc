import html
import json
import sys
import os
import logging

# Configure Python path for imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
parent_dir = os.path.abspath(os.path.join(BASE_DIR, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import streamlit.components.v1 as components
import base64
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Import backend modules with error handling
try:
    from backend.knowledge import ingest_knowledge_source
except ImportError as e:
    logging.error(f"Failed to import backend.knowledge: {e}")
    ingest_knowledge_source = None

try:
    from backend.document_extractors import SUPPORTED_FILE_TYPES
except ImportError as e:
    logging.error(f"Failed to import backend.document_extractors: {e}")
    SUPPORTED_FILE_TYPES = {"pdf": (["pdf"], "PDF"), "docx": (["docx"], "DOCX"), "txt": (["txt"], "TXT")}

try:
    from backend.hitl import list_pending_reviews, resolve_review
except ImportError as e:
    logging.error(f"Failed to import backend.hitl: {e}")
    list_pending_reviews = None
    resolve_review = None

try:
    from backend.mas_engine import ask
except ImportError as e:
    logging.error(f"Failed to import backend.mas_engine: {e}")
    ask = None

try:
    from backend.guardrails import setting as guardrail_setting
except ImportError as e:
    logging.error(f"Failed to import backend.guardrails: {e}")
    guardrail_setting = None

try:
    from backend.voice_assistant import (
        StreamingTranscriptBuffer,
        VoiceSession,
        VoiceStateMachine,
        analyze_voice_turn,
        create_voice_session,
        normalize_voice_language,
        transcribe_with_whisper,
        whisper_stt_enabled,
        synthesize_with_openai,
        openai_audio_enabled,
    )
except ImportError as e:
    logging.error(f"Failed to import backend.voice_assistant: {e}")
    normalize_voice_language = lambda lang, text=None: "auto"
    transcribe_with_whisper = lambda audio, language: (None, "Voice service unavailable")
    whisper_stt_enabled = lambda: False
    synthesize_with_openai = lambda content, response_language: (None, "TTS service unavailable")
    openai_audio_enabled = lambda: False

    class StreamingTranscriptBuffer:
        def __init__(self):
            self._buffer = ""

        def push_chunk(self, chunk):
            return {"text": chunk or "", "is_final": True, "partial": ""}

        def reset(self):
            self._buffer = ""

    class VoiceStateMachine:
        def __init__(self):
            self.state = "Idle"
            self.history = []

        def handle(self, event):
            self.state = "Listening" if event == "user_speaking" else self.state
            self.history.append(event)
            return self.state

    class VoiceSession:
        def __init__(self):
            self.language = "en"
            self.emotion = "neutral"
            self.urgency = "low"
            self.context = []
            self.last_intent = "general"
            self.last_entities = []
            self.conversation_summary = ""

        def update_user_turn(self, text, metadata=None):
            return self.snapshot()

        def snapshot(self):
            return {
                "language": self.language,
                "emotion": self.emotion,
                "urgency": self.urgency,
                "context": list(self.context),
                "last_intent": self.last_intent,
                "last_entities": list(self.last_entities),
                "conversation_summary": self.conversation_summary,
                "memory": {
                    "language": self.language,
                    "emotion": self.emotion,
                    "urgency": self.urgency,
                    "last_intent": self.last_intent,
                    "last_entities": list(self.last_entities),
                    "conversation_summary": self.conversation_summary,
                },
            }

    def analyze_voice_turn(text, metadata=None):
        return {"emotion": "neutral", "urgency": "low"}

    def create_voice_session():
        return VoiceSession()

try:
    from streamlit_mic_recorder import mic_recorder, speech_to_text
except ImportError as e:
    logging.info(f"streamlit_mic_recorder not available: {e}")
    mic_recorder = None
    speech_to_text = None


st.set_page_config(
    page_title="CSC Mitra - CSC AI Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSC_LOGO_URL = "https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Common_Service_Centres_Logo.svg/512px-Common_Service_Centres_Logo.svg.png"

QUICK_PROMPTS = (
    ("🌾 PM Kisan Sahayata", "PM Kisan registration ka process batao"),
    ("🪪 PAN Card Seva", "PAN correction process batao"),
    ("💳 DigiPay Guide", "How to use DigiPay for cash withdrawal"),
    ("👷 e-Shram Registration", "e-Shram registration ke liye documents kya hain"),
)

RECENT_QUESTIONS = (
    "PM Kisan registration process",
    "PAN correction steps",
    "DigiPay settlement help",
    "Ayushman card eligibility",
)

INGEST_SOURCE_TYPES = ("URL", "PDF", "DOCX", "TXT", "CSV", "XLSX", "PPTX")


def _escape(value):
    return html.escape(str(value), quote=True)


def _init_state():
    defaults = {
        "messages": [],
        "chat_draft": "",
        "voice_mode": False,
        "voice_status": "",
        "admin_unlocked": False,
        "message_seq": 0,
        "last_voice_transcript": "",
        "last_audio_id": "",
        "autoplay_message_id": None,
        "show_ingestion": False,
        "sidebar_quick_query": "",
        "tts_voice_choice": "Bhashini (default)",
        "tts_audio_cache": {},
        "voice_state_machine": None,
        "voice_transcript_buffer": None,
        "voice_session": None,
        "voice_last_state": "Idle",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    for message in st.session_state.messages:
        if "id" not in message:
            st.session_state.message_seq += 1
            message["id"] = st.session_state.message_seq

    if st.session_state.get("voice_state_machine") is None:
        st.session_state["voice_state_machine"] = VoiceStateMachine()
    if st.session_state.get("voice_transcript_buffer") is None:
        st.session_state["voice_transcript_buffer"] = StreamingTranscriptBuffer()
    if st.session_state.get("voice_session") is None:
        st.session_state["voice_session"] = create_voice_session()


def _append_message(role, content):
    st.session_state.message_seq += 1
    message = {
        "id": st.session_state.message_seq,
        "ts": datetime.utcnow().isoformat() + "Z",
        "role": role,
        "content": content,
    }
    st.session_state.messages.append(message)
    return message


def _apply_css():
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');

    :root {
        --csc-blue: #005bac;
        --csc-orange: #ff6b00;
        --ink: #111827;
        --muted: #4b5563;
        --line: #e5e7eb;
        --panel: #ffffff;
        --soft-green: #f0fdf4;
    }

    html, body, [class*="css"], .stMarkdown, .stTextInput, .stTextArea, .stButton, .stSelectbox {
        font-family: Inter, "Noto Sans Devanagari", "Nirmala UI", "Mangal", system-ui, sans-serif;
    }

    .stApp {
        background: #f8fafc;
        color: var(--ink);
    }

    .block-container {
        max-width: 900px;
        padding-top: 2.1rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #f1f5f9;
        border-right: 1px solid var(--line);
    }

    .app-hero {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        margin: 4px 0 22px 0;
        padding: 20px 22px;
    }

    .app-hero h1 {
        color: #03447a;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 0;
        line-height: 1.16;
        margin: 0 0 6px 0;
    }

    .app-hero p {
        color: #1e3a8a;
        font-size: .98rem;
        font-weight: 500;
        line-height: 1.58;
        margin: 0;
    }

    .soft-divider {
        border-top: 1px solid var(--line);
        margin: 22px 0;
    }

    .section-label {
        color: var(--ink);
        font-size: .9rem;
        font-weight: 800;
        margin: 0 0 10px 0;
    }

    .recent-list {
        color: #475569;
        font-size: .94rem;
        line-height: 1.85;
        margin-bottom: 10px;
    }

    .sidebar-brand {
        margin-bottom: 18px;
    }

    .sidebar-brand h2 {
        color: var(--ink);
        font-size: 1.08rem;
        font-weight: 800;
        letter-spacing: 0;
        line-height: 1.25;
        margin: 8px 0 0 0;
    }

    .sidebar-brand p {
        color: var(--muted);
        font-size: .84rem;
        line-height: 1.35;
        margin: 3px 0 0 0;
    }

    .sidebar-status {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        color: #166534;
        font-size: .86rem;
        font-weight: 750;
        line-height: 1.65;
        padding: 12px;
        text-align: center;
    }

    .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
    }

    .hero-badge, .voice-status {
        align-items: center;
        border-radius: 999px;
        display: inline-flex;
        font-size: .82rem;
        font-weight: 700;
        gap: 6px;
        min-height: 34px;
        padding: 7px 11px;
        white-space: nowrap;
    }

    .hero-badge {
        background: #ffffff;
        border: 1px solid var(--line);
        color: #334155;
    }

    .voice-status {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        margin: 6px 0 10px 0;
    }

    .pulse-dot {
        animation: pulse 1.15s ease-in-out infinite;
        background: #ef4444;
        border-radius: 999px;
        display: inline-block;
        height: 9px;
        width: 9px;
    }

    @keyframes pulse {
        0%, 100% { opacity: .35; transform: scale(.82); }
        50% { opacity: 1; transform: scale(1.1); }
    }

    .prompt-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 6px 0 14px 0;
    }

    [data-testid="stChatMessage"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 10px 26px rgba(15, 23, 42, .045);
        margin-bottom: 12px;
        padding: 10px 12px;
    }

    [data-testid="stChatMessageContent"] {
        line-height: 1.64;
    }

    textarea {
        border-radius: 8px !important;
        border-color: #cbd5e1 !important;
        font-size: 1rem !important;
        min-height: 80px !important;
    }

    .stButton > button {
        border-radius: 8px;
        min-height: 42px;
        font-weight: 750;
    }

    div[data-testid="stHorizontalBlock"] .stButton > button {
        background: #ffffff;
        border: 1px solid #d8dee8;
        box-shadow: 0 8px 18px rgba(15, 23, 42, .035);
    }

    div[data-testid="stHorizontalBlock"] .stButton > button:hover {
        border-color: var(--csc-blue);
        color: var(--csc-blue);
        background: #f8fafc;
    }

    .stButton > button[kind="primary"] {
        background: #16a34a;
        border-color: #16a34a;
    }

    .stButton > button[kind="primary"]:hover {
        background: #15803d;
        border-color: #15803d;
    }

    .empty-state {
        background: transparent;
        border: 0;
        border-radius: 8px;
        color: var(--muted);
        padding: 4px 0 12px 0;
        text-align: left;
    }

    .ingestion-panel {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 16px 34px rgba(15, 23, 42, .08);
        margin: 12px 0;
        padding: 16px;
    }

    .ingest-stage {
        color: var(--muted);
        font-size: .9rem;
        margin: 6px 0 2px 0;
    }

    .ingest-ready {
        color: #15803d;
        font-size: .95rem;
        font-weight: 600;
        margin-top: 8px;
    }

    .small-note {
        color: var(--muted);
        font-size: .86rem;
        line-height: 1.45;
        margin-top: 8px;
    }

    @media (max-width: 760px) {
        .block-container {
            padding-left: .85rem;
            padding-right: .85rem;
        }

        .app-hero {
            align-items: flex-start;
            flex-direction: column;
            padding: 16px;
        }

        .hero-badges {
            justify-content: flex-start;
        }

        .app-hero h1 {
            font-size: 1.45rem;
        }
    }
</style>
""",
        unsafe_allow_html=True,
    )


def _browser_speech_html(text, language_code, voice_tone="Bhashini (default)", autoplay=False):
    safe_text = json.dumps(text[:5000]).replace("</", "<\\/")
    safe_lang = json.dumps(language_code)
    safe_tone = json.dumps(voice_tone)
    auto = "true" if autoplay else "false"
    return f"""
<button id="listenBtn" type="button" aria-label="Listen to assistant response">Listen to Response</button>
<button id="stopBtn" type="button" aria-label="Stop reading assistant response">Stop</button>
<span id="listenStatus" aria-live="polite"></span>
<style>
    body {{
        margin: 0;
        background: transparent;
        font-family: Inter, system-ui, sans-serif;
    }}
    #listenBtn, #stopBtn {{
        align-items: center;
        background: #ffffff;
        border: 1px solid #d6dde8;
        border-radius: 8px;
        color: #1e293b;
        cursor: pointer;
        display: inline-flex;
        font-size: 13px;
        font-weight: 700;
        gap: 6px;
        min-height: 34px;
        padding: 7px 11px;
    }}
    #stopBtn {{
        margin-left: 6px;
    }}
    #listenBtn:hover, #stopBtn:hover {{
        border-color: #005bac;
        color: #005bac;
    }}
    #listenStatus {{
        color: #4b5563;
        font-size: 12px;
        margin-left: 8px;
    }}
</style>
<script>
    const answerText = {safe_text};
    const lang = {safe_lang};
    const shouldAutoplay = {auto};
    const button = document.getElementById("listenBtn");
    const stopButton = document.getElementById("stopBtn");
    const status = document.getElementById("listenStatus");
    let queue = [];
    let activeIndex = 0;

    function chooseVoice() {{
        const voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
        const matching = voices.filter((voice) => voice.lang && voice.lang.toLowerCase().startsWith(lang.slice(0, 2).toLowerCase()));
        const tone = {safe_tone}.toLowerCase();
        const tonePatterns = [];

        if (tone.includes("bhashini")) {{
            tonePatterns.push(/bhashini|bharat|india|hindi|hindustan/i);
        }} else if (tone.includes("openai nova")) {{
            tonePatterns.push(/alloy|nova|natural|english|united states|en-us/i);
        }} else if (tone.includes("gemini-like")) {{
            tonePatterns.push(/natural|neural|google|microsoft|zira|ravi|maya|ariel/i);
        }} else if (tone.includes("microsoft copilot")) {{
            tonePatterns.push(/microsoft|copilot|zira|ariel|maya|david|chloe/i);
        }}

        let friendly = null;
        for (const pattern of tonePatterns) {{
            friendly = matching.find((voice) => pattern.test(voice.name || ""));
            if (friendly) break;
        }}

        if (!friendly) {{
            friendly = matching.find((voice) => /natural|neural|google|microsoft|zira|heera|ravi/i.test(voice.name || ""));
        }}

        return friendly || matching[0] || voices[0] || null;
    }}

    function speechChunks(text) {{
        const cleaned = text
            .replace(/https?:\\/\\/\\S+/g, "official link available in the answer")
            .replace(/[*#`_>-]/g, "")
            .replace(/\\s+/g, " ")
            .trim();
        const sentences = cleaned.match(/[^.!?।]+[.!?।]?/g) || [cleaned];
        const chunks = [];
        let current = "";
        for (const sentence of sentences) {{
            const next = (current + " " + sentence.trim()).trim();
            if (next.length > 220 && current) {{
                chunks.push(current);
                current = sentence.trim();
            }} else {{
                current = next;
            }}
        }}
        if (current) chunks.push(current);
        return chunks.slice(0, 14);
    }}

    function stopSpeech(message = "") {{
        queue = [];
        activeIndex = 0;
        if ("speechSynthesis" in window) {{
            window.speechSynthesis.cancel();
        }}
        status.textContent = message;
    }}

    function speakChunk() {{
        if (activeIndex >= queue.length) {{
            status.textContent = "";
            return;
        }}
        const utterance = new SpeechSynthesisUtterance(queue[activeIndex]);
        utterance.lang = lang;
        utterance.rate = tone.includes("bhashini") ? 0.92 : 0.86;
        utterance.pitch = tone.includes("gemini-like") ? 1.08 : 1.04;
        utterance.volume = 1.0;
        const voice = chooseVoice();
        if (voice) utterance.voice = voice;
        utterance.onstart = () => status.textContent = "Speaking...";
        utterance.onend = () => {{
            activeIndex += 1;
            window.setTimeout(speakChunk, 140);
        }};
        utterance.onerror = () => stopSpeech("Unable to play voice.");
        window.speechSynthesis.speak(utterance);
    }}

    function speak() {{
        if (!("speechSynthesis" in window)) {{
            status.textContent = "Speech not supported in this browser.";
            return;
        }}
        stopSpeech("");
        queue = speechChunks(answerText);
        activeIndex = 0;
        speakChunk();
    }}

    button.addEventListener("click", speak);
    stopButton.addEventListener("click", () => stopSpeech("Stopped."));
    if (shouldAutoplay) {{
        setTimeout(speak, 450);
    }}
</script>
"""


def _render_header():
    st.markdown(
        """
<div class="app-hero">
    <h1>CSC Mitra – CSC AI Assistant</h1>
    <p>Namaste. Ask about CSC services and government schemes in Hindi or English. You will get simple, polite, official-source guidance step by step.</p>
</div>
<div style="font-size:0.9rem;color:#6b7280;margin-top:8px;margin-bottom:14px;">DPDP Compliance: This service uses official sources; personal data is handled per policy.</div>
""",
        unsafe_allow_html=True,
    )


def _html_to_data_url(html_str: str) -> str:
    """Encode raw HTML into a data: URL for use with `st.iframe`.

    Streamlit 1.58+ prefers `st.iframe` over raw components.html in some
    hosted environments; convert the HTML to base64 data URL so iframe
    can render it safely.
    """
    b = html_str.encode("utf-8")
    b64 = base64.b64encode(b).decode("ascii")
    return f"data:text/html;base64,{b64}"


def _render_quick_prompts():
    st.markdown("### Quick prompts")
    cols = st.columns(len(QUICK_PROMPTS))
    for (label, prompt), col in zip(QUICK_PROMPTS, cols):
        if col.button(label, use_container_width=True, key=f"quick_prompt_{label}"):
            return prompt
        col.caption(prompt)
    return ""


def _render_sidebar():
    with st.sidebar:
        st.title("Settings")
        st.markdown("Fine-tune how CSC Mitra responds.")
        cloud_consent = st.checkbox(
            "Allow cloud-based response generation",
            value=st.session_state.get("cloud_consent", True),
            help="Enable cloud processing for better answer quality.",
            key="cloud_consent",
        )
        response_language = st.selectbox(
            "Response language",
            ["Auto", "English", "Hindi"],
            index=["Auto", "English", "Hindi"].index(
                st.session_state.get("response_language", "Auto")
            ),
            key="response_language",
        )
        st.checkbox(
            "🔊 Voice mode",
            key="voice_mode",
            help="Play answers aloud when available.",
        )
        st.selectbox(
            "Voice tone",
            [
                "Bhashini (default)",
                "OpenAI Nova",
                "Gemini-like (neural)",
                "Microsoft Copilot (neural)",
            ],
            index=[
                "Bhashini (default)",
                "OpenAI Nova",
                "Gemini-like (neural)",
                "Microsoft Copilot (neural)",
            ].index(st.session_state.get("tts_voice_choice", "Bhashini (default)")),
            key="tts_voice_choice",
        )
        st.markdown("---")
        st.markdown("Use the chat box below, or tap any quick prompt card.")
    return cloud_consent, response_language, response_language, ""


def _query_admin_mode():

    try:
        value = st.query_params.get("admin", "")
    except Exception:
        value = ""

    return str(value).lower() in {"1", "true", "yes"}


def _admin_attachment_visible():

    return st.session_state.admin_unlocked or _query_admin_mode()


def _render_ingestion_panel(cloud_consent=True):

    if not st.session_state.show_ingestion or not _admin_attachment_visible():
        return

    st.markdown(
        """
<div class="ingestion-panel">
    <strong>Add Knowledge Source</strong>
    <div class="small-note">Ingest official CSC documents and government service guidelines into the knowledge base.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    source_type = st.radio(
        "Source Type",
        INGEST_SOURCE_TYPES,
        horizontal=True,
        key="ingest_source_type",
    )
    source_key = source_type.lower()

    official_url = st.text_input(
        "Official URL",
        key="official_ingest_url",
        placeholder="https://pmkisan.gov.in/...",
    )

    uploaded_file = None
    if source_key != "url":
        file_types = SUPPORTED_FILE_TYPES[source_key][0]
        uploaded_file = st.file_uploader(
            "Upload File",
            type=file_types,
            key=f"official_{source_key}_upload",
        )

    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        department = st.text_input("Department (optional)", key="ingest_department", placeholder="Agriculture")
    with meta_col2:
        service_type = st.text_input("Service Type (optional)", key="ingest_service", placeholder="PM-KISAN")

    source_name = st.text_input(
        "Source Name (optional)",
        key="ingest_source_name",
        placeholder="PM-KISAN Operational Guidelines",
    )

    progress_bar = st.progress(0)
    stage_label = st.empty()

    ingest_col, close_col = st.columns([2, 1])
    with ingest_col:
        if st.button("Ingest", type="primary", use_container_width=True):
            def _on_progress(stage, percent):
                progress_bar.progress(min(max(float(percent), 0.0), 1.0))
                if stage == "Knowledge Ready":
                    stage_label.markdown('<div class="ingest-ready">✓ Knowledge Ready</div>', unsafe_allow_html=True)
                else:
                    stage_label.markdown(f'<div class="ingest-stage">{stage}...</div>', unsafe_allow_html=True)

            _on_progress("Uploading", 0.05)

            status = ingest_knowledge_source(
                source_key,
                official_url=official_url.strip(),
                uploaded_file=uploaded_file,
                cloud_consent=cloud_consent,
                human_reviewed=True,
                department=department.strip(),
                service_type=service_type.strip(),
                source_name=source_name.strip(),
                progress_callback=_on_progress,
            )

            lowered = status.lower()
            if "failed" in lowered or "blocked" in lowered or "not stored" in lowered or "could not" in lowered:
                st.warning(status)
            else:
                st.success(status)

    with close_col:
        if st.button("Close", use_container_width=True):
            st.session_state.show_ingestion = False
            st.rerun()

    st.divider()
    with st.expander("Human Review Queue", expanded=False):
        pending_reviews = list_pending_reviews(limit=5)
        if not pending_reviews:
            st.caption("No pending human-review items.")
        for item in pending_reviews:
            review_id = item["id"]
            st.markdown(f"**CSC-HITL-{review_id}** · {item['reason']} · confidence {item['confidence']:.2f}")
            st.caption(item["created_at"])
            st.markdown(f"**User query**\n\n{item['query']}")
            if item.get("draft_response"):
                st.markdown(f"**Draft response**\n\n{item['draft_response'][:1200]}")
            if st.button("Mark reviewed", key=f"resolve_hitl_{review_id}"):
                if resolve_review(review_id, operator_note="Reviewed from Streamlit admin panel"):
                    st.success(f"CSC-HITL-{review_id} marked reviewed.")
                    st.rerun()
                else:
                    st.warning("Could not update this review item.")


def _render_voice_status():
    status = st.session_state.voice_status
    if status:
        st.markdown(
            f"""
<div class="voice-status">
    <span class="pulse-dot"></span>
    {_escape(status)}
</div>
""",
            unsafe_allow_html=True,
        )


def _render_listen_control(message, response_language, voice_mode):
    content = message["content"]
    language_code = normalize_voice_language(response_language, content)
    voice_tone = st.session_state.get("tts_voice_choice", "Bhashini (default)")
    autoplay = st.session_state.autoplay_message_id == message["id"]

    # If a server-side TTS provider is configured, use it for reliable playback.
    # Cache generated audio per message id to avoid repeated calls.
    cache = st.session_state.get("tts_audio_cache", {})
    cache_key = f"msg_{message.get('id')}"
    if openai_audio_enabled():
        audio_bytes = cache.get(cache_key)
        if not audio_bytes:
            with st.spinner("Generating voice..."):
                audio_bytes, err = synthesize_with_openai(content, response_language)
            if audio_bytes:
                cache[cache_key] = audio_bytes
                st.session_state["tts_audio_cache"] = cache
            else:
                st.error(f"TTS Error: {err}")
                # Fallback to browser synthesis below
        if audio_bytes:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.audio(audio_bytes, format="audio/mp3")
            with col2:
                st.caption(f"🎵 {voice_tone}")
            st.session_state.autoplay_message_id = None
            return

    # Fallback to browser speech synthesis (may be blocked by browser autoplay policies)
    data_url = _html_to_data_url(_browser_speech_html(content, language_code, voice_tone=voice_tone, autoplay=autoplay))
    st.iframe(data_url, height=88)

    if autoplay:
        st.session_state.autoplay_message_id = None


def _render_chat_history(response_language, voice_mode):
    if not st.session_state.messages:
        return

    for message in st.session_state.messages:
        ts = message.get("ts")
        ts_display = f" · {ts}" if ts else ""
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            st.markdown(f"<div style='font-size:0.8rem;color:#6b7280'>Posted{ts_display}</div>", unsafe_allow_html=True)
            if message["role"] == "assistant":
                # Speaker button to play assistant reply on demand
                col1, col2 = st.columns([8, 1])
                with col2:
                    if st.button("🔊", key=f"play_{message.get('id')}"):
                        st.session_state.autoplay_message_id = message.get("id")
                        st.rerun()
                _render_listen_control(message, response_language, voice_mode)


def _recent_questions():

    user_questions = [
        item.get("content", "").strip()
        for item in st.session_state.messages
        if item.get("role") == "user" and item.get("content", "").strip()
    ]
    if user_questions:
        return user_questions[-4:][::-1]

    return RECENT_QUESTIONS


def _queue_voice_transcript(transcript, voice_mode):
    clean_text = (transcript or "").strip()
    if not clean_text:
        return

    st.session_state.last_voice_transcript = clean_text
    st.session_state.voice_status = "Processing your speech..."

    machine = st.session_state.get("voice_state_machine")
    if machine is not None:
        machine.handle("final_transcript")
        st.session_state.voice_last_state = machine.state

    session = st.session_state.get("voice_session")
    if session is not None:
        session.update_user_turn(clean_text)

    if voice_mode:
        st.session_state.pending_voice_submit = clean_text
        st.session_state.clear_composer_next = True
    else:
        st.session_state.voice_prefill = clean_text

    st.rerun()


def _render_microphone(response_language, voice_mode):
    language_code = normalize_voice_language(response_language, st.session_state.chat_draft or "")

    # Short, clear prompts for recorder components (avoid emoji images)
    start_prompt_text = "Mic"
    stop_prompt_text = "Listening..."

    if speech_to_text is not None and not whisper_stt_enabled():
        try:
            transcript = speech_to_text(
                language=language_code,
                start_prompt=start_prompt_text,
                stop_prompt=stop_prompt_text,
                just_once=True,
                use_container_width=True,
                key="csc_web_speech",
            )
        except TypeError:
            transcript = speech_to_text(
                language=language_code,
                start_prompt=start_prompt_text,
                stop_prompt=stop_prompt_text,
                just_once=True,
                key="csc_web_speech",
            )
        if transcript and transcript.strip() != st.session_state.last_voice_transcript:
            _queue_voice_transcript(transcript, voice_mode)
        return

    if whisper_stt_enabled() and mic_recorder is not None:
        try:
            audio = mic_recorder(
                start_prompt=start_prompt_text,
                stop_prompt=stop_prompt_text,
                just_once=True,
                use_container_width=True,
                key="csc_whisper_recorder",
            )
        except TypeError:
            audio = mic_recorder(
                start_prompt=start_prompt_text,
                stop_prompt=stop_prompt_text,
                just_once=True,
                key="csc_whisper_recorder",
            )
        if audio:
            # audio may be a dict-like object from the recorder
            audio_bytes = None
            if isinstance(audio, dict):
                audio_bytes = audio.get("bytes")
                audio_id = str(audio.get("id") or hash(audio_bytes))
            else:
                audio_id = str(getattr(audio, "id", hash(audio)))
            if audio_bytes is None:
                # nothing to process
                return
            if audio_id != st.session_state.last_audio_id:
                st.session_state.last_audio_id = audio_id
                machine = st.session_state.get("voice_state_machine")
                if machine is not None:
                    machine.handle("user_speaking")
                    st.session_state.voice_last_state = machine.state
                with st.spinner("Processing your spoken words..."):
                    transcript, error = transcribe_with_whisper(audio_bytes, language_code)
                if error:
                    st.session_state.voice_status = ""
                    st.toast("⚠ Voice service busy. Please try again in a few seconds.")
                else:
                    buffer = st.session_state.get("voice_transcript_buffer")
                    if buffer is not None:
                        buffer.reset()
                        buffer.push_chunk(transcript)
                    _queue_voice_transcript(transcript, voice_mode)
        return

    if speech_to_text is not None:
        try:
            transcript = speech_to_text(
                language=language_code,
                start_prompt=start_prompt_text,
                stop_prompt=stop_prompt_text,
                just_once=True,
                use_container_width=True,
                key="csc_web_speech",
            )
        except TypeError:
            transcript = speech_to_text(
                language=language_code,
                start_prompt=start_prompt_text,
                stop_prompt=stop_prompt_text,
                just_once=True,
                key="csc_web_speech",
            )
        if transcript and transcript.strip() != st.session_state.last_voice_transcript:
            _queue_voice_transcript(transcript, voice_mode)
        return

    st.button("Mic", disabled=True, use_container_width=True, help="Microphone input needs streamlit-mic-recorder.")


def _render_composer(response_language, voice_mode):
    if st.session_state.get("voice_prefill"):
        st.session_state.chat_draft = st.session_state.pop("voice_prefill")
        st.session_state.voice_status = ""

    if st.session_state.get("clear_composer_next"):
        st.session_state.chat_draft = ""
        st.session_state.clear_composer_next = False

    _render_voice_status()

    query = st.chat_input(
        placeholder="Type your CSC question and press Enter...",
        key="chat_draft",
    )

    admin_visible = _admin_attachment_visible()
    if admin_visible:
        mic_col, send_col, attach_col = st.columns([1, 3, 1], vertical_alignment="center")
    else:
        mic_col, send_col = st.columns([1, 3], vertical_alignment="center")

    with mic_col:
        _render_microphone(response_language, voice_mode)

    with send_col:
        send_clicked = st.button(
            "Send",
            type="primary",
            use_container_width=True,
            disabled=not (st.session_state.chat_draft or "").strip(),
        )

    if admin_visible:
        with attach_col:
            if st.button("📎", use_container_width=True, key="admin_attachment"):
                st.session_state.show_ingestion = not st.session_state.show_ingestion
                st.rerun()

    manual_query = (st.session_state.chat_draft or "").strip() if send_clicked else ""
    voice_query = st.session_state.pop("pending_voice_submit", "")
    return voice_query or query or manual_query


def _build_answer(query, cloud_consent, response_language, voice_mode):
    clean_query = (query or "").strip()
    if not clean_query:
        return

    history = st.session_state.messages[-8:]
    _append_message("user", clean_query)

    language_map = {"Auto": "auto", "English": "en", "Hindi": "hi"}
    # Ensure `ask` is available; try a lazy import if the top-level import failed.
    global ask
    if ask is None:
        try:
            from backend.mas_engine import ask as _ask
            ask = _ask
        except Exception as e:
            logging.error(f"Unable to import backend.mas_engine.ask: {e}")
            st.error("Assistant unavailable — backend service could not be loaded.")
            return

    with st.spinner("Finding a simple, reliable answer for you..."):
        answer = ask(
            clean_query,
            cloud_consent=cloud_consent,
            history=history,
            response_language=language_map[response_language],
            fast_mode=voice_mode,
        )

    assistant_message = _append_message("assistant", answer)
    st.session_state.autoplay_message_id = assistant_message["id"] if voice_mode else None
    st.session_state.voice_status = ""
    st.session_state.clear_composer_next = True
    st.rerun()


def _render_realtime_voice():
    st.markdown("## 🎙️ Real-Time Voice Assistant")
    st.markdown("Click the button below to start a live voice conversation.")
    
    html_code = """
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  body {
    margin: 0;
    padding: 0;
    font-family: 'Inter', sans-serif;
    background: transparent;
  }
  .voice-card {
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .voice-card:hover {
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  }
  .controls {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
  }
  .btn {
    border: none;
    padding: 10px 20px;
    font-size: 15px;
    font-weight: 600;
    border-radius: 9999px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Inter', sans-serif;
  }
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: scale(1) !important;
  }
  .btn-primary {
    background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
    color: white;
    box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
  }
  .btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
  }
  .btn-danger {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
    box-shadow: 0 4px 14px 0 rgba(239, 68, 68, 0.39);
  }
  .btn-danger:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
  }
  .btn-secondary {
    background: white;
    color: #4b5563;
    border: 1px solid #d1d5db;
  }
  .btn-secondary:hover:not(:disabled) {
    background: #f9fafb;
    color: #111827;
  }
  .status-container {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f1f5f9;
    padding: 8px 16px;
    border-radius: 9999px;
    font-size: 13px;
    color: #475569;
    font-weight: 500;
    margin-bottom: 16px;
    border: 1px solid #e2e8f0;
  }
  .pulse-dot {
    height: 10px;
    width: 10px;
    background-color: #94a3b8;
    border-radius: 50%;
    display: inline-block;
  }
  .is-active .pulse-dot {
    background-color: #22c55e;
    animation: pulse-green 1.5s infinite;
  }
  .is-listening .pulse-dot {
    background-color: #ef4444;
    animation: pulse-red 1.5s infinite;
  }
  @keyframes pulse-green {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
    70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
  }
  @keyframes pulse-red {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
    70% { transform: scale(1.2); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  }
  .transcript-box {
    width: 100%;
    background: white;
    border-radius: 12px;
    padding: 16px;
    min-height: 90px;
    max-height: 150px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .message {
    line-height: 1.5;
    font-size: 14px;
  }
  .msg-you { color: #64748b; }
  .msg-ai { color: #0f172a; font-weight: 500; }
  .msg-error {
    color: #ef4444;
    background: #fef2f2;
    padding: 12px;
    border-radius: 8px;
    font-size: 13px;
    border: 1px solid #fecaca;
  }
</style>
</head>
<body>
<div class="voice-card">
  <div class="controls">
    <button id="startBtn" class="btn btn-primary">
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
      Start Voice Mode
    </button>
    <button id="stopBtn" class="btn btn-secondary" disabled>Stop</button>
    <button id="bargeInBtn" class="btn btn-danger" disabled>
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path></svg>
      Interrupt
    </button>
  </div>
  
  <div id="statusContainer" class="status-container">
    <span id="pulseDot" class="pulse-dot"></span>
    <span id="status">Disconnected</span>
  </div>
  
  <div class="transcript-box" id="transcriptBox">
    <div class="message msg-you" style="text-align: center; margin-top: 10px;">Ready to chat! Press Start Voice Mode.</div>
  </div>
</div>

<script>
  let ws = null, audioContext = null, mediaStream = null, processor = null, isRecording = false;
  const startBtn = document.getElementById('startBtn'), stopBtn = document.getElementById('stopBtn'),
        bargeInBtn = document.getElementById('bargeInBtn'), statusDiv = document.getElementById('status'),
        transcriptBox = document.getElementById('transcriptBox'), statusContainer = document.getElementById('statusContainer');
        
  function addMessage(text, type) {
    if (transcriptBox.innerHTML.includes("Ready to chat!")) transcriptBox.innerHTML = "";
    if (type === "error") {
      transcriptBox.innerHTML = `<div class="message msg-error">${text}</div>`;
    } else if (type === "you") {
      transcriptBox.innerHTML += `<div class="message msg-you"><strong>You:</strong> ${text}</div>`;
    } else if (type === "ai") {
      transcriptBox.innerHTML += `<div class="message msg-ai"><strong>AI:</strong> ${text}</div>`;
    }
    transcriptBox.scrollTop = transcriptBox.scrollHeight;
  }
        
  function setStatus(text, state) {
    statusDiv.innerText = text;
    statusContainer.className = 'status-container ' + state;
  }
        
  startBtn.onclick = async () => {
    try {
      ws = new WebSocket('ws://localhost:8000/ws/audio');
      ws.onopen = () => {
        setStatus("Connected. Listening...", "is-listening");
        startBtn.disabled = true; stopBtn.disabled = false; bargeInBtn.disabled = false;
        startRecording();
      };
      ws.onmessage = async (event) => {
        if (typeof event.data === "string") {
          let data = JSON.parse(event.data);
          if (data.type === "status") {
             if (data.message.includes("Speaking")) setStatus(data.message, "is-active");
             else if (data.message.includes("Listening") || data.message.includes("Thinking")) setStatus(data.message, "is-listening");
             else setStatus(data.message, "");
          }
          else if (data.type === "transcript") addMessage(data.text, "you");
          else if (data.type === "response") addMessage(data.text, "ai");
          else if (data.type === "error") addMessage(data.message, "error");
        } else {
          playAudio(event.data);
        }
      };
      ws.onclose = () => {
        setStatus("Disconnected", "");
        startBtn.disabled = false; stopBtn.disabled = true; bargeInBtn.disabled = true;
        stopRecording();
      };
    } catch (e) { setStatus("Error connecting", ""); addMessage("Could not connect to backend", "error"); }
  };
  stopBtn.onclick = () => { if (ws) ws.close(); };
  bargeInBtn.onclick = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({type: "barge_in"}));
      setStatus("Interrupted. Listening again...", "is-listening");
    }
  };
  async function startRecording() {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(mediaStream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);
    processor.onaudioprocess = (e) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      const inputData = e.inputBuffer.getChannelData(0);
      const pcmData = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        let s = Math.max(-1, Math.min(1, inputData[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      ws.send(pcmData.buffer);
    };
    source.connect(processor); processor.connect(audioContext.destination);
  }
  function stopRecording() {
    if (processor) { processor.disconnect(); processor = null; }
    if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }
    if (audioContext) { audioContext.close(); audioContext = null; }
  }
  
  
  async function playAudio(data) {
    try {
      if (!audioContext) {
         audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioContext.state === 'suspended') {
         await audioContext.resume();
      }
      const arrayBuffer = await new Blob([data]).arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start(0);
    } catch (e) {
      console.error("Web Audio API failed, falling back to HTML5 Audio:", e);
      try {
        const blob = new Blob([data], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        await audio.play();
      } catch (err) {
        addMessage("Speaker blocked by browser. Please click anywhere on the page to enable audio.", "error");
      }
    }
  }
</script>


</body>
</html>
"""
    data_url = _html_to_data_url(html_code)
    st.iframe(data_url, height=360)


def _set_voice_mode(value):
    """Callback for the mic/chat icon buttons.

    `voice_mode` is the session_state key bound to the sidebar checkbox
    widget (see _render_sidebar). Streamlit forbids assigning to a
    widget-bound key from the main script body after that widget has
    already been instantiated in the same run -- doing so raises
    StreamlitAPIException. Callbacks run *before* the script reruns and
    any widgets are instantiated, so this is the safe way to change it.
    """
    st.session_state.voice_mode = value


_init_state()
_apply_css()
cloud_consent, response_language, voice_language, sidebar_query = _render_sidebar()
voice_mode = st.session_state.voice_mode
_render_header()
# Quick mode selector icons: 🎤 Mic for voice, 💬 Chat for text
col_icon, _ = st.columns([1, 9])
with col_icon:
    st.button("🎤 Mic", key="icon_mic", on_click=_set_voice_mode, args=(True,))
    st.button("💬 Chat", key="icon_chat", on_click=_set_voice_mode, args=(False,))
quick_prompt_query = sidebar_query or _render_quick_prompts()
_render_chat_history(response_language, voice_mode)
_render_realtime_voice()
submitted_query = quick_prompt_query or _render_composer(response_language, voice_mode)
_render_ingestion_panel(cloud_consent)

if submitted_query:
    _build_answer(submitted_query, cloud_consent, response_language, voice_mode)
