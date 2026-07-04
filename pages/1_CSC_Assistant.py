"""
CSC Assistant Page
Multi-agent powered assistant for service discovery and workflow guidance
"""

import streamlit as st
import sys
import os

# ── path setup ──────────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.join(current_dir, "..")
backend_dir = os.path.join(parent_dir, "backend")
for path in (parent_dir, backend_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

# ── backend import ───────────────────────────────────────────────────────────
try:
    from backend.mas_engine import ask
    BACKEND_AVAILABLE = True
except ImportError:
    try:
        from mas_engine import ask
        BACKEND_AVAILABLE = True
    except ImportError:
        BACKEND_AVAILABLE = False

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CSC Assistant",
    page_icon="🤖",
    layout="wide",
)

# ── session state defaults ───────────────────────────────────────────────────
for key, default in {
    "conversation_history": [],
    "assistant_prefill":    "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.response-box {
    background: #f0f9ff;
    border-left: 4px solid #0ea5e9;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin-top: 0.5rem;
    font-size: 0.97rem;
    line-height: 1.7;
}
.error-box {
    background: #fff1f2;
    border-left: 4px solid #f43f5e;
    padding: 0.8rem 1.25rem;
    border-radius: 8px;
    margin-top: 0.5rem;
}
.hist-q { font-weight: 600; color: #0f172a; }
.hist-a { color: #1e293b; margin-top: 0.3rem; }
</style>
""", unsafe_allow_html=True)

# ── header ───────────────────────────────────────────────────────────────────
st.markdown("# 🤖 CSC Assistant")
st.markdown("Intelligent assistant powered by multi-agent architecture")
st.divider()

# ── two-column info + quick prompts ──────────────────────────────────────────
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("## Capabilities")
    st.markdown("""
- 🔍 **Service Discovery**: Find relevant services  
- 📋 **Eligibility Check**: Verify eligibility  
- 📄 **Document Guide**: Required documents  
- 📞 **Workflow Guidance**: Step-by-step instructions  
""")

with col2:
    st.markdown("## Quick Prompts")
    quick_prompts = [
        "PM Kisan registration process",
        "PAN card correction steps",
        "e-Shram registration requirements",
        "DigiPay cash withdrawal guide",
    ]
    qcols = st.columns(2)
    for i, prompt in enumerate(quick_prompts):
        if qcols[i % 2].button(prompt, use_container_width=True, key=f"qp_{i}"):
            st.session_state.assistant_prefill = prompt

# ── main input ───────────────────────────────────────────────────────────────
st.divider()
st.markdown("## 🎙️ Real-Time Voice Assistant")
st.markdown("Click the button below to start a live voice conversation.")

# Real-Time Voice WebRTC/WebSocket Component
import streamlit.components.v1 as components

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

components.html(html_code, height=360)

st.divider()
st.markdown("## 💬 Ask Your Question")

# ── validation helpers ────────────────────────────────────────────────────────
def _validate_query(q: str):
    """Return (is_valid, error_message)."""
    q = q.strip()
    if not q:
        return False, "⚠️ Please enter a question before submitting."
    if len(q) < 5:
        return False, "⚠️ Query is too short. Please ask a complete question (at least 5 characters)."
    if len(q) > 1000:
        return False, "⚠️ Query is too long (max 1000 characters). Please shorten your question."
    if q.replace(" ", "").isnumeric():
        return False, "⚠️ Please ask a meaningful question, not just numbers."
    return True, ""

user_query = st.text_area(
    "Enter your query:",
    value=st.session_state.assistant_prefill,
    placeholder="Ask about any CSC service or scheme...",
    height=110,
    key="assistant_query_area",
)

# clear pre-fill after it has been loaded into the widget
st.session_state.assistant_prefill = ""

btn_col, _ = st.columns([1, 5])
submit = btn_col.button("🚀 Get Assistant Response", use_container_width=True)

if submit:
    is_valid, err_msg = _validate_query(user_query or "")

    if not is_valid:
        st.markdown(f'<div class="error-box">{err_msg}</div>', unsafe_allow_html=True)

    elif not BACKEND_AVAILABLE:
        st.error(
            "⚠️ Backend unavailable: `backend.mas_engine` could not be imported. "
            "Check that all backend files are present and dependencies are installed."
        )

    else:
        # ── pull settings from sidebar (set by streamlit_app.py) if available ──
        cloud_consent     = st.session_state.get("cloud_consent", True)
        response_language = st.session_state.get("response_language", "Auto")
        language_map      = {"Auto": "auto", "English": "en", "Hindi": "hi"}

        # ── build a short history list from conversation_history ─────────────
        history = []
        for q_text, a_text in st.session_state.conversation_history[-4:]:
            history.append({"role": "user",      "content": q_text})
            history.append({"role": "assistant",  "content": a_text})

        with st.spinner("🔄 Processing your query using multi-agent architecture…"):
            try:
                answer = ask(
                    user_query.strip(),
                    cloud_consent=cloud_consent,
                    history=history,
                    response_language=language_map.get(response_language, "auto"),
                    fast_mode=False,
                )
                if not answer or not answer.strip():
                    answer = (
                        "I could not find verified information for that query. "
                        "Please try rephrasing or ask about a specific CSC service."
                    )
            except Exception as exc:
                answer = None
                st.markdown(
                    f'<div class="error-box">❌ An error occurred while processing your query: '
                    f'<code>{exc}</code></div>',
                    unsafe_allow_html=True,
                )

        if answer:
            st.markdown("### ✅ Response")
            st.markdown(f'<div class="response-box">{answer}</div>', unsafe_allow_html=True)

            # ── save to conversation history ──────────────────────────────────
            st.session_state.conversation_history.append(
                (user_query.strip(), answer)
            )

# ── conversation history ─────────────────────────────────────────────────────
st.divider()
st.markdown("## 📜 Conversation History")

if st.session_state.conversation_history:
    if st.button("🗑️ Clear History", key="clear_hist"):
        st.session_state.conversation_history = []
        st.rerun()

    for i, (question, answer) in enumerate(
        reversed(st.session_state.conversation_history)
    ):
        label = f"Q{len(st.session_state.conversation_history) - i}: {question[:60]}{'…' if len(question) > 60 else ''}"
        with st.expander(label, expanded=(i == 0)):
            st.markdown(f'<div class="hist-q">Q: {question}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="hist-a">{answer}</div>', unsafe_allow_html=True)
else:
    st.info("No conversation history yet. Ask your first question!")
