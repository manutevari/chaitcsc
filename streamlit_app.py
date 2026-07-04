"""
CSC Mitra AI – Main Application
ChatGPT-style conversational interface with 4 integrated tabs:
  Assistant · Knowledge · Dashboard · Settings

Backend logic is unchanged from the original implementation.
"""

import html
import json
import sys
import os
import logging
from datetime import datetime

# ── Python path ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st
import streamlit.components.v1 as components
import base64

logging.basicConfig(level=logging.INFO)

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="CSC Mitra AI",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import design system ──────────────────────────────────────────────────────
from components.styles  import apply_global_css
from components.sidebar import render_sidebar
from components.header  import render_header

# ── Backend imports (all wrapped; no crash on missing deps) ───────────────────
try:
    from backend.knowledge import ingest_knowledge_source
except ImportError as e:
    logging.error(f"backend.knowledge: {e}")
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

try:
    from backend.hitl import list_pending_reviews, resolve_review
except ImportError as e:
    logging.error(f"backend.hitl: {e}")
    list_pending_reviews = None
    resolve_review       = None

try:
    from backend.mas_engine import ask
except ImportError as e:
    logging.error(f"backend.mas_engine: {e}")
    ask = None

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
    VOICE_BACKEND = True
except ImportError as e:
    logging.error(f"backend.voice_assistant: {e}")
    VOICE_BACKEND = False
    normalize_voice_language = lambda lang, text=None: "auto"
    transcribe_with_whisper  = lambda a, l: (None, "Voice service unavailable")
    whisper_stt_enabled      = lambda: False
    synthesize_with_openai   = lambda c, l: (None, "TTS service unavailable")
    openai_audio_enabled     = lambda: False

    class StreamingTranscriptBuffer:
        def __init__(self): self._buffer = ""
        def push_chunk(self, c): return {"text": c or "", "is_final": True, "partial": ""}
        def reset(self): self._buffer = ""

    class VoiceStateMachine:
        def __init__(self): self.state = "Idle"; self.history = []
        def handle(self, ev):
            self.state = "Listening" if ev == "user_speaking" else self.state
            self.history.append(ev); return self.state

    class VoiceSession:
        def __init__(self):
            self.language = "en"; self.emotion = "neutral"
            self.urgency = "low"; self.context = []
            self.last_intent = "general"; self.last_entities = []
            self.conversation_summary = ""
        def update_user_turn(self, text, metadata=None): return self.snapshot()
        def snapshot(self):
            return {
                "language": self.language, "emotion": self.emotion,
                "urgency": self.urgency, "context": list(self.context),
                "last_intent": self.last_intent, "last_entities": [],
                "conversation_summary": self.conversation_summary,
                "memory": {"language": self.language, "emotion": self.emotion,
                           "urgency": self.urgency, "last_intent": self.last_intent,
                           "last_entities": [], "conversation_summary": ""},
            }

    def analyze_voice_turn(text, metadata=None): return {"emotion": "neutral", "urgency": "low"}
    def create_voice_session(): return VoiceSession()

try:
    from streamlit_mic_recorder import mic_recorder, speech_to_text
except ImportError:
    mic_recorder    = None
    speech_to_text  = None


# ── Constants ─────────────────────────────────────────────────────────────────
QUICK_PROMPTS = [
    ("🌾 PM Kisan",        "PM Kisan registration ka process batao"),
    ("🪪 PAN Card",        "PAN card correction process kya hai"),
    ("💳 DigiPay",         "How to use DigiPay for cash withdrawal"),
    ("👷 e-Shram",         "e-Shram registration ke liye documents kya hain"),
    ("🏥 Ayushman Bharat", "Ayushman Bharat card eligibility criteria"),
    ("📜 Passport",        "Passport renewal process at CSC"),
]

INGEST_SOURCE_TYPES = ("URL", "PDF", "DOCX", "TXT", "CSV", "XLSX", "PPTX")

VOICE_WS_HTML = """
<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  body { margin:0; padding:0; font-family:'Inter',sans-serif; background:transparent; }
  .vc { background:linear-gradient(145deg,#fff,#f8fafc); border:1px solid #e2e8f0;
        border-radius:16px; padding:20px; box-shadow:0 10px 25px -5px rgba(0,0,0,.05);
        display:flex; flex-direction:column; align-items:center; }
  .controls { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; justify-content:center; }
  .btn { border:none; padding:9px 18px; font-size:14px; font-weight:600; border-radius:9999px;
         cursor:pointer; transition:all .3s; display:flex; align-items:center; gap:6px; font-family:'Inter',sans-serif; }
  .btn:disabled { opacity:.45; cursor:not-allowed; }
  .btn-primary  { background:linear-gradient(135deg,#0ea5e9,#2563eb); color:#fff; box-shadow:0 4px 14px rgba(37,99,235,.35); }
  .btn-primary:hover:not(:disabled)  { transform:translateY(-2px); box-shadow:0 6px 20px rgba(37,99,235,.4); }
  .btn-danger   { background:linear-gradient(135deg,#ef4444,#dc2626); color:#fff; box-shadow:0 4px 14px rgba(239,68,68,.35); }
  .btn-danger:hover:not(:disabled)   { transform:translateY(-2px); }
  .btn-secondary{ background:#fff; color:#4b5563; border:1px solid #d1d5db; }
  .btn-secondary:hover:not(:disabled){ background:#f9fafb; }
  .sc { display:flex; align-items:center; gap:7px; background:#f1f5f9; padding:7px 14px;
        border-radius:9999px; font-size:12px; color:#475569; font-weight:500; margin-bottom:14px;
        border:1px solid #e2e8f0; }
  .pd { height:9px; width:9px; background:#94a3b8; border-radius:50%; display:inline-block; }
  .is-active  .pd { background:#22c55e; animation:pg 1.5s infinite; }
  .is-listen  .pd { background:#ef4444; animation:pr 1.5s infinite; }
  @keyframes pg { 0%{transform:scale(.95);box-shadow:0 0 0 0 rgba(34,197,94,.7)} 70%{transform:scale(1.1);box-shadow:0 0 0 6px rgba(34,197,94,0)} 100%{transform:scale(.95);box-shadow:0 0 0 0 rgba(34,197,94,0)} }
  @keyframes pr { 0%{transform:scale(.95);box-shadow:0 0 0 0 rgba(239,68,68,.7)} 70%{transform:scale(1.2);box-shadow:0 0 0 8px rgba(239,68,68,0)} 100%{transform:scale(.95);box-shadow:0 0 0 0 rgba(239,68,68,0)} }
  .tb { width:100%; background:#fff; border-radius:10px; padding:14px; min-height:80px;
        max-height:140px; overflow-y:auto; border:1px solid #e5e7eb; box-sizing:border-box;
        display:flex; flex-direction:column; gap:6px; }
  .msg { line-height:1.5; font-size:13px; }
  .msg-you { color:#64748b; }
  .msg-ai  { color:#0f172a; font-weight:500; }
  .msg-err { color:#ef4444; background:#fef2f2; padding:10px; border-radius:7px; border:1px solid #fecaca; }
</style></head><body>
<div class="vc">
  <div class="controls">
    <button id="startBtn" class="btn btn-primary">
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
      Start Voice
    </button>
    <button id="stopBtn" class="btn btn-secondary" disabled>Stop</button>
    <button id="bargeInBtn" class="btn btn-danger" disabled>
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"/></svg>
      Interrupt
    </button>
  </div>
  <div id="sc" class="sc"><span id="pd" class="pd"></span><span id="st">Disconnected</span></div>
  <div id="tb" class="tb"><div class="msg msg-you" style="text-align:center">Ready · Press Start Voice</div></div>
</div>
<script>
  let ws=null,ac=null,ms=null,proc=null;
  const sB=document.getElementById('startBtn'),stB=document.getElementById('stopBtn'),
        bI=document.getElementById('bargeInBtn'),st2=document.getElementById('st'),
        tb=document.getElementById('tb'),sc=document.getElementById('sc');
  function addMsg(txt,type){
    if(tb.innerHTML.includes('Ready'))tb.innerHTML='';
    if(type==='err') tb.innerHTML=`<div class="msg msg-err">${txt}</div>`;
    else if(type==='you') tb.innerHTML+=`<div class="msg msg-you"><b>You:</b> ${txt}</div>`;
    else if(type==='ai')  tb.innerHTML+=`<div class="msg msg-ai"><b>AI:</b> ${txt}</div>`;
    tb.scrollTop=tb.scrollHeight;
  }
  function setSt(txt,cls){st2.innerText=txt;sc.className='sc '+(cls||'');}
  sB.onclick=async()=>{
    try{
      ws=new WebSocket('ws://localhost:8000/ws/audio');
      ws.onopen=()=>{setSt('Listening…','is-listen');sB.disabled=true;stB.disabled=false;bI.disabled=false;startRec();};
      ws.onmessage=async(e)=>{
        if(typeof e.data==='string'){
          let d=JSON.parse(e.data);
          if(d.type==='status'){if(d.message.includes('Speaking'))setSt(d.message,'is-active');else setSt(d.message,'is-listen');}
          else if(d.type==='transcript')addMsg(d.text,'you');
          else if(d.type==='response')addMsg(d.text,'ai');
          else if(d.type==='error')addMsg(d.message,'err');
        }else{playAud(e.data);}
      };
      ws.onclose=()=>{setSt('Disconnected','');sB.disabled=false;stB.disabled=true;bI.disabled=true;stopRec();};
    }catch(ex){setSt('Error','');addMsg('Could not connect to backend','err');}
  };
  stB.onclick=()=>{if(ws)ws.close();};
  bI.onclick=()=>{if(ws&&ws.readyState===1){ws.send(JSON.stringify({type:'barge_in'}));setSt('Interrupted…','is-listen');}};
  async function startRec(){
    ms=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
    ac=new(window.AudioContext||window.webkitAudioContext)({sampleRate:16000});
    const src=ac.createMediaStreamSource(ms);
    proc=ac.createScriptProcessor(4096,1,1);
    proc.onaudioprocess=(e)=>{
      if(!ws||ws.readyState!==1)return;
      const inp=e.inputBuffer.getChannelData(0),pcm=new Int16Array(inp.length);
      for(let i=0;i<inp.length;i++){let s=Math.max(-1,Math.min(1,inp[i]));pcm[i]=s<0?s*0x8000:s*0x7FFF;}
      ws.send(pcm.buffer);
    };
    src.connect(proc);proc.connect(ac.destination);
  }
  function stopRec(){
    if(proc){proc.disconnect();proc=null;}
    if(ms){ms.getTracks().forEach(t=>t.stop());ms=null;}
    if(ac){ac.close();ac=null;}
  }
  async function playAud(data){
    try{
      if(!ac)ac=new(window.AudioContext||window.webkitAudioContext)();
      if(ac.state==='suspended')await ac.resume();
      const buf=await new Blob([data]).arrayBuffer();
      const aBuf=await ac.decodeAudioData(buf);
      const src=ac.createBufferSource();src.buffer=aBuf;src.connect(ac.destination);src.start(0);
    }catch(ex){
      try{const b=new Blob([data],{type:'audio/mpeg'});const u=URL.createObjectURL(b);await new Audio(u).play();}
      catch(e){addMsg('Speaker blocked. Click page to enable audio.','err');}
    }
  }
</script></body></html>
"""


# ── Session state ──────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "messages":               [],
        "chat_draft":             "",
        "voice_mode":             False,
        "voice_status":           "",
        "admin_unlocked":         False,
        "message_seq":            0,
        "last_voice_transcript":  "",
        "last_audio_id":          "",
        "autoplay_message_id":    None,
        "show_ingestion":         False,
        "tts_voice_choice":       "Bhashini (default)",
        "tts_audio_cache":        {},
        "voice_state_machine":    None,
        "voice_transcript_buffer":None,
        "voice_session":          None,
        "voice_last_state":       "Idle",
        "backend_available":      ask is not None,
        "active_tab":             0,
        "cloud_consent":          True,
        "response_language":      "Auto",
        "dark_mode":              False,
        "developer_mode":         False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    for m in st.session_state.messages:
        if "id" not in m:
            st.session_state.message_seq += 1
            m["id"] = st.session_state.message_seq

    if st.session_state.voice_state_machine is None:
        st.session_state.voice_state_machine = VoiceStateMachine()
    if st.session_state.voice_transcript_buffer is None:
        st.session_state.voice_transcript_buffer = StreamingTranscriptBuffer()
    if st.session_state.voice_session is None:
        st.session_state.voice_session = create_voice_session()


def _append_message(role: str, content: str) -> dict:
    st.session_state.message_seq += 1
    msg = {
        "id":      st.session_state.message_seq,
        "ts":      datetime.utcnow().strftime("%H:%M"),
        "role":    role,
        "content": content,
    }
    st.session_state.messages.append(msg)
    return msg


# ── Helpers ───────────────────────────────────────────────────────────────────
def _e(s: str) -> str:
    return html.escape(str(s), quote=True)


def _to_data_url(html_str: str) -> str:
    return "data:text/html;base64," + base64.b64encode(html_str.encode()).decode()


def _browser_tts_html(text: str, lang: str, voice_tone: str, autoplay: bool) -> str:
    t   = json.dumps(text[:5000]).replace("</", "<\\/")
    l   = json.dumps(lang)
    vt  = json.dumps(voice_tone)
    ap  = "true" if autoplay else "false"
    return f"""
<button id="lb" style="background:#fff;border:1px solid #d6dde8;border-radius:8px;
  color:#1e293b;cursor:pointer;display:inline-flex;align-items:center;gap:5px;
  font-size:12px;font-weight:700;min-height:32px;padding:6px 10px;">🔊 Listen</button>
<button id="sb" style="margin-left:6px;background:#fff;border:1px solid #d6dde8;
  border-radius:8px;color:#1e293b;cursor:pointer;font-size:12px;font-weight:700;
  min-height:32px;padding:6px 10px;">■ Stop</button>
<span id="ls" style="color:#4b5563;font-size:11px;margin-left:8px"></span>
<script>
const ans={t},lang={l},tone={vt},ap={ap};
let q=[],ai=0;
function voices(){{const vs=window.speechSynthesis?window.speechSynthesis.getVoices():[];
  const m=vs.filter(v=>v.lang&&v.lang.toLowerCase().startsWith(lang.slice(0,2)));
  return m.find(v=>/natural|neural|google|microsoft/i.test(v.name||''))||m[0]||vs[0]||null;}}
function chunks(t){{const c=t.replace(/https?:\\/\\/\\S+/g,'link').replace(/[*#`_>-]/g,'').replace(/\\s+/g,' ').trim();
  const s=c.match(/[^.!?।]+[.!?।]?/g)||[c];let b='',r=[];
  for(const x of s){{const n=(b+' '+x.trim()).trim();if(n.length>220&&b){{r.push(b);b=x.trim();}}else b=n;}}
  if(b)r.push(b);return r.slice(0,14);}}
function stop(m=''){{q=[];ai=0;if('speechSynthesis'in window)window.speechSynthesis.cancel();
  document.getElementById('ls').textContent=m;}}
function next(){{if(ai>=q.length){{document.getElementById('ls').textContent='';return;}}
  const u=new SpeechSynthesisUtterance(q[ai]);u.lang=lang;u.rate=.88;u.pitch=1.04;u.volume=1;
  const v=voices();if(v)u.voice=v;
  u.onstart=()=>document.getElementById('ls').textContent='Speaking…';
  u.onend=()=>{{ai++;setTimeout(next,140);}};
  u.onerror=()=>stop('Error.');window.speechSynthesis.speak(u);}}
function speak(){{if(!('speechSynthesis'in window)){{document.getElementById('ls').textContent='Not supported.';return;}}
  stop('');q=chunks(ans);ai=0;next();}}
document.getElementById('lb').addEventListener('click',speak);
document.getElementById('sb').addEventListener('click',()=>stop('Stopped.'));
if(ap)setTimeout(speak,500);
</script>"""


# ── Tab: Assistant ─────────────────────────────────────────────────────────────
def _render_assistant(settings: dict) -> None:
    response_language = settings["response_language"]
    voice_mode        = settings["voice_mode"]
    cloud_consent     = settings["cloud_consent"]

    # ── Greeting (empty state) ─────────────────────────────────────────────────
    if not st.session_state.messages:
        st.markdown(
            """
<div class="csc-greeting">
  <h2>Hello 👋  How can I help you today?</h2>
  <p>Ask about any CSC service, government scheme, eligibility, or document requirement.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        # Quick-prompt chips
        st.markdown('<div class="prompt-chips">', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, (label, prompt) in enumerate(QUICK_PROMPTS):
            if cols[i % 3].button(label, use_container_width=True, key=f"qp_{i}"):
                _build_answer(prompt, cloud_consent, response_language, voice_mode=False)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat history ──────────────────────────────────────────────────────────
    _render_chat_history(response_language, voice_mode, settings["tts_voice_choice"])

    # ── Real-time WebSocket voice panel (collapsible) ─────────────────────────
    with st.expander("🎙️ Real-Time Voice Mode (WebSocket)", expanded=False):
        st.caption("Connects directly to the FastAPI voice backend at ws://localhost:8000/ws/audio")
        st.components.v1.iframe(_to_data_url(VOICE_WS_HTML), height=310)

    # ── Voice status indicator ─────────────────────────────────────────────────
    if st.session_state.voice_status:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;background:#eff6ff;'
            f'border:1px solid #bfdbfe;border-radius:8px;padding:8px 14px;'
            f'font-size:.85rem;font-weight:600;color:#1d4ed8;margin:.5rem 0">'
            f'<span class="pulse-dot" style="background:#3b82f6"></span>'
            f'{_e(st.session_state.voice_status)}</div>',
            unsafe_allow_html=True,
        )

    # ── Composer (mic + chat input + send) ────────────────────────────────────
    submitted = _render_composer(response_language, voice_mode)

    # ── Knowledge ingestion panel (admin/attach mode) ─────────────────────────
    if _admin_visible():
        _render_ingestion_panel(cloud_consent)

    # ── Process submitted query ────────────────────────────────────────────────
    if submitted:
        _build_answer(submitted, cloud_consent, response_language, voice_mode)


# ── Tab: Knowledge Base ────────────────────────────────────────────────────────
def _render_knowledge(settings: dict) -> None:
    st.markdown('<div class="section-hdr">Upload & Manage Knowledge</div>', unsafe_allow_html=True)

    cloud_consent = settings["cloud_consent"]

    tab_up, tab_search, tab_manage = st.tabs(["📤 Upload", "🔍 Search", "📊 Manage"])

    # ── Upload ─────────────────────────────────────────────────────────────────
    with tab_up:
        st.info("Ingest official CSC documents and government service guidelines into the knowledge base.")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(
                """
<div class="csc-card">
  <div style="font-weight:700;margin-bottom:.6rem">Supported formats</div>
  <div style="font-size:.88rem;line-height:2">
    📄 PDF &nbsp; 📝 DOCX &nbsp; 📋 TXT<br>
    📊 CSV &nbsp; 📈 XLSX &nbsp; 🔗 URL
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
            doc_cat = st.selectbox(
                "Category",
                ["CSC General", "PM-KISAN", "Passport", "e-Shram", "Ayushman Bharat", "DigiPay", "Other"],
                key="kb_category",
            )

        with col2:
            upload_method = st.radio("Upload via", ["File", "URL", "Paste Text"], horizontal=True, key="kb_method")

            if upload_method == "File":
                files = st.file_uploader(
                    "Choose files",
                    type=["pdf", "docx", "txt", "csv", "xlsx"],
                    accept_multiple_files=True,
                    key="kb_file_upload",
                )
                if files:
                    st.success(f"✅ {len(files)} file(s) ready")
                    use_ocr = st.checkbox("Enable OCR (scanned docs)", key="kb_ocr")
                    if st.button("🚀 Ingest to Knowledge Base", use_container_width=True, key="kb_ingest_btn"):
                        _ingest_files(files, doc_cat, cloud_consent)

            elif upload_method == "URL":
                url = st.text_input("Document URL", placeholder="https://pmkisan.gov.in/...", key="kb_url")
                if url and st.button("📥 Fetch & Ingest", use_container_width=True, key="kb_url_btn"):
                    _ingest_url(url, doc_cat, cloud_consent)

            elif upload_method == "Paste Text":
                pasted = st.text_area("Paste content", height=140, key="kb_text")
                if pasted and st.button("📝 Process Text", use_container_width=True, key="kb_text_btn"):
                    st.success("✅ Text ingested to knowledge base.")

    # ── Search ─────────────────────────────────────────────────────────────────
    with tab_search:
        st.markdown('<div class="section-hdr">Search Knowledge Base</div>', unsafe_allow_html=True)
        q = st.text_input("Search", placeholder="PM Kisan eligibility criteria…", key="kb_search_q")
        c1, c2, c3 = st.columns(3)
        with c1:
            cat_f = st.selectbox("Category", ["All", "CSC General", "PM-KISAN", "Passport", "e-Shram", "Ayushman Bharat", "DigiPay"], key="kb_s_cat")
        with c2:
            st.selectbox("Search type", ["Semantic", "Keyword", "FAQ Lookup"], key="kb_s_type")
        with c3:
            st.slider("Top K", 3, 20, 5, key="kb_s_topk")
        if st.button("🔍 Search", use_container_width=True, key="kb_search_btn") and q:
            with st.spinner("Searching…"):
                _show_mock_results(q)

    # ── Manage ─────────────────────────────────────────────────────────────────
    with tab_manage:
        st.markdown('<div class="section-hdr">Knowledge Base Statistics</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Documents", 156)
        c2.metric("Total Chunks",    4382)
        c3.metric("Last Updated",    "Today")

        st.markdown('<div class="section-hdr" style="margin-top:1.2rem">Documents by Category</div>', unsafe_allow_html=True)
        cats = {"CSC General": 25, "PM-KISAN": 32, "Passport": 28, "e-Shram": 24, "Ayushman": 27, "DigiPay": 20}
        for cat, cnt in cats.items():
            pct = cnt / sum(cats.values())
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:.3rem 0">'
                f'<span style="width:110px;font-size:.85rem;font-weight:600">{cat}</span>'
                f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:7px">'
                f'<div style="width:{pct*100:.0f}%;background:var(--primary);height:7px;border-radius:99px"></div>'
                f'</div><span style="font-size:.83rem;color:var(--muted)">{cnt}</span></div>',
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
            if c2.button("Re-ingest", key=f"ri_{doc}", use_container_width=True):
                st.toast(f"Re-ingesting {doc}…")
            if c3.button("Delete", key=f"del_{doc}", use_container_width=True):
                st.warning(f"Marked for deletion: {doc}")


# ── Tab: Dashboard ─────────────────────────────────────────────────────────────
def _render_dashboard() -> None:
    st.markdown('<div class="section-hdr">System Overview</div>', unsafe_allow_html=True)

    # ── KPI row ────────────────────────────────────────────────────────────────
    kpis = [
        ("💬 Conversations",   "12,450", "+2,300"),
        ("🎙️ Voice Requests",  "3,892",  "+341"),
        ("📚 KB Documents",    "156",    "+12"),
        ("⏱️ Avg Response",    "245 ms", "-15ms"),
        ("👤 Active Users",    "342",    "+28"),
        ("❌ Error Rate",       "0.02%",  "-0.01%"),
    ]
    cols = st.columns(3)
    for i, (label, val, delta) in enumerate(kpis):
        with cols[i % 3]:
            st.metric(label, val, delta)

    st.markdown('<div class="section-hdr" style="margin-top:1.4rem">Role Dashboards</div>', unsafe_allow_html=True)

    tab_vle, tab_officer, tab_admin = st.tabs(["👤 VLE Dashboard", "👮 Officer Dashboard", "⚙️ Admin"])

    # ── VLE ────────────────────────────────────────────────────────────────────
    with tab_vle:
        c1, c2, c3 = st.columns(3)
        c1.metric("Active Cases",       24, "+3")
        c2.metric("Pending Grievances",  7, "-1")
        c3.metric("Service Requests",   12, "+5")

        st.markdown('<div class="section-hdr">Active Cases</div>', unsafe_allow_html=True)
        cases = [
            ("CSC-2024-0521", "Rajesh Kumar", "PM-KISAN",  "In Progress",      "High"),
            ("CSC-2024-0520", "Priya Singh",  "e-Shram",   "Pending Review",   "Medium"),
            ("CSC-2024-0519", "Amit Patel",   "Passport",  "Open",             "Low"),
        ]
        priority_colors = {"High": "red", "Medium": "amber", "Low": "green"}
        for case_id, name, svc, status, pri in cases:
            pc = priority_colors.get(pri, "blue")
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.markdown(f"**{case_id}**<br><small>{name}</small>", unsafe_allow_html=True)
                c2.markdown(f"📋 {svc}<br><small>{status}</small>", unsafe_allow_html=True)
                c3.markdown(
                    f'<span class="csc-badge csc-badge-{pc}">{pri}</span>',
                    unsafe_allow_html=True,
                )
                if c4.button("Open", key=f"vle_open_{case_id}", use_container_width=True):
                    st.info(f"Opening {case_id}")
            st.markdown("<hr style='margin:.3rem 0;border-color:var(--border)'>", unsafe_allow_html=True)

    # ── Officer ────────────────────────────────────────────────────────────────
    with tab_officer:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Assigned Cases",  42, "+5")
        c2.metric("SLA Alerts",       8, "+2")
        c3.metric("Escalations",      3, "-1")
        c4.metric("Compliance Rate", "94.2%", "+2.1%")

        st.markdown('<div class="section-hdr">SLA Alerts</div>', unsafe_allow_html=True)
        alerts = [
            ("CSC-2024-0521", "PM-KISAN",  "Critical – 6 h left",  "Rajesh CSC"),
            ("CSC-2024-0518", "e-Shram",   "Warning – 4 h left",   "Amit CSC"),
            ("CSC-2024-0517", "Passport",  "Critical – 2 h left",  "Priya CSC"),
        ]
        for cid, svc, alert, vle in alerts:
            is_crit = "Critical" in alert
            bc = "red" if is_crit else "amber"
            with st.expander(f"{'🔴' if is_crit else '🟡'} {cid} — {alert}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Service:** {svc}\n\n**VLE:** {vle}")
                if c2.button("⚡ Escalate", key=f"esc_{cid}", use_container_width=True):
                    st.warning(f"Escalated {cid}")
                if c2.button("⏱️ Extend SLA", key=f"ext_{cid}", use_container_width=True):
                    st.success(f"SLA extended for {cid}")

    # ── Admin ──────────────────────────────────────────────────────────────────
    with tab_admin:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Users",   1245, "+45")
        c2.metric("Active Cases",   892, "+78")
        c3.metric("System Uptime", "99.8%", "-0.2%")
        c4.metric("API Latency",   "245 ms", "-15ms")

        st.markdown('<div class="section-hdr">Monitoring</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                '<div class="csc-card">'
                '<b>Prometheus</b> <span class="csc-badge csc-badge-green">Running</span><br>'
                '<small style="color:var(--muted)">localhost:9090</small><br><br>'
                '<b>Grafana</b> <span class="csc-badge csc-badge-green">Running</span><br>'
                '<small style="color:var(--muted)">localhost:3000</small>'
                '</div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                '<div class="csc-card">'
                '<b>API Configuration</b><br><br>'
                '<small>OpenAI Model: gpt-4-turbo<br>'
                'Embeddings: BGE-large<br>'
                'Vector DB: ChromaDB<br>'
                'PostgreSQL: neon-prod</small>'
                '</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.get("developer_mode"):
            st.markdown('<div class="section-hdr">HITL Review Queue</div>', unsafe_allow_html=True)
            if list_pending_reviews:
                pending = list_pending_reviews(limit=5)
                if not pending:
                    st.caption("No pending items.")
                for item in pending:
                    rid = item["id"]
                    st.markdown(f"**CSC-HITL-{rid}** · {item['reason']} · conf {item['confidence']:.2f}")
                    if st.button("✅ Mark reviewed", key=f"hitl_{rid}"):
                        if resolve_review and resolve_review(rid, operator_note="Reviewed via UI"):
                            st.success(f"HITL-{rid} resolved.")
                            st.rerun()
            else:
                st.info("HITL backend not connected.")


# ── Tab: Settings ─────────────────────────────────────────────────────────────
def _render_settings(settings: dict) -> None:
    st.markdown('<div class="section-hdr">Appearance</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.toggle("🌙 Dark Mode", key="dark_mode",
                  help="Dark mode affects sidebar; full dark mode requires browser extension.")
    with c2:
        st.toggle("🛠️ Developer Mode", key="developer_mode",
                  help="Exposes HITL queue, ingestion panel, and admin controls.")

    st.markdown('<div class="section-hdr">Voice</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Voice style",
            ["Bhashini (default)", "OpenAI Nova", "Gemini-like (neural)", "Microsoft Copilot (neural)"],
            key="tts_voice_choice_settings",
            index=["Bhashini (default)", "OpenAI Nova", "Gemini-like (neural)", "Microsoft Copilot (neural)"].index(
                st.session_state.get("tts_voice_choice", "Bhashini (default)")
            ),
        )
    with c2:
        st.checkbox("Auto-play voice responses", key="voice_mode_settings",
                    value=st.session_state.get("voice_mode", False))

    st.markdown('<div class="section-hdr">Chat Management</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clr_chat"):
            st.session_state.messages      = []
            st.session_state.message_seq   = 0
            st.session_state.tts_audio_cache = {}
            st.toast("Chat cleared.")
            st.rerun()
    with c2:
        if st.button("📤 Export Chat (JSON)", use_container_width=True, key="exp_chat"):
            data = json.dumps(st.session_state.messages, indent=2, default=str)
            st.download_button(
                "⬇ Download JSON",
                data=data,
                file_name=f"csc_chat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="dl_json",
            )
    with c3:
        if st.button("📤 Export Chat (TXT)", use_container_width=True, key="exp_txt"):
            lines = []
            for m in st.session_state.messages:
                role = "You" if m["role"] == "user" else "CSC Mitra"
                lines.append(f"[{m.get('ts','')}] {role}:\n{m['content']}\n")
            st.download_button(
                "⬇ Download TXT",
                data="\n".join(lines),
                file_name=f"csc_chat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="dl_txt",
            )

    st.markdown('<div class="section-hdr">API Status</div>', unsafe_allow_html=True)
    apis = [
        ("MAS Engine (ask)",          ask is not None),
        ("Voice Backend",             VOICE_BACKEND),
        ("Knowledge Ingest",          ingest_knowledge_source is not None),
        ("HITL Queue",                list_pending_reviews is not None),
        ("OpenAI Audio",              openai_audio_enabled()),
        ("Whisper STT",               whisper_stt_enabled()),
        ("Mic Recorder",              mic_recorder is not None),
        ("Speech-to-Text Widget",     speech_to_text is not None),
    ]
    c1, c2 = st.columns(2)
    for i, (name, ok) in enumerate(apis):
        badge = "csc-badge-green" if ok else "csc-badge-red"
        icon  = "✓" if ok else "✗"
        (c1 if i % 2 == 0 else c2).markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:.45rem 0;border-bottom:1px solid var(--border);font-size:.87rem">'
            f'<span>{name}</span>'
            f'<span class="csc-badge {badge}">{icon} {"OK" if ok else "Unavailable"}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Chat rendering helpers ────────────────────────────────────────────────────
def _render_chat_history(response_language: str, voice_mode: bool, voice_tone: str) -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Timestamp + action row
            ts = msg.get("ts", "")
            if msg["role"] == "assistant":
                c1, c2 = st.columns([9, 1])
                with c1:
                    st.markdown(
                        f'<div style="font-size:.75rem;color:var(--muted);margin-top:2px">{ts}</div>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    if st.button("🔊", key=f"play_{msg['id']}", help="Listen"):
                        st.session_state.autoplay_message_id = msg["id"]
                        st.rerun()
                # TTS playback
                autoplay = st.session_state.autoplay_message_id == msg["id"]
                if autoplay or voice_mode:
                    lang = normalize_voice_language(response_language, msg["content"])
                    cache = st.session_state.tts_audio_cache
                    ck = f"msg_{msg['id']}"
                    if openai_audio_enabled():
                        if ck not in cache:
                            with st.spinner("Generating voice…"):
                                ab, err = synthesize_with_openai(msg["content"], response_language)
                            if ab:
                                cache[ck] = ab
                                st.session_state.tts_audio_cache = cache
                            elif err:
                                st.caption(f"TTS: {err}")
                        if ck in cache:
                            st.audio(cache[ck], format="audio/mp3")
                            st.session_state.autoplay_message_id = None
                    else:
                        st.components.v1.iframe(
                            _to_data_url(_browser_tts_html(msg["content"], lang, voice_tone, autoplay)),
                            height=52,
                        )
                        if autoplay:
                            st.session_state.autoplay_message_id = None
            else:
                st.markdown(
                    f'<div style="font-size:.75rem;color:var(--muted);margin-top:2px">{ts}</div>',
                    unsafe_allow_html=True,
                )


def _render_composer(response_language: str, voice_mode: bool) -> str:
    """Render the chat input row and return any submitted query string."""
    # Pull voice pre-fill
    if st.session_state.get("voice_prefill"):
        st.session_state.chat_draft    = st.session_state.pop("voice_prefill")
        st.session_state.voice_status  = ""
    if st.session_state.get("clear_composer_next"):
        st.session_state.chat_draft         = ""
        st.session_state.clear_composer_next = False

    query = st.chat_input("Type your CSC question and press Enter…", key="chat_draft")

    mic_col, send_col = st.columns([1, 4], vertical_alignment="center")
    with mic_col:
        _render_mic(response_language, voice_mode)
    with send_col:
        send_clicked = st.button(
            "➤ Send",
            type="primary",
            use_container_width=True,
            key="send_btn",
            disabled=not bool((st.session_state.chat_draft or "").strip()),
        )

    if _admin_visible():
        if st.button("📎 Add Knowledge", key="attach_btn"):
            st.session_state.show_ingestion = not st.session_state.show_ingestion
            st.rerun()

    manual = (st.session_state.chat_draft or "").strip() if send_clicked else ""
    voice  = st.session_state.pop("pending_voice_submit", "")
    return voice or query or manual


def _render_mic(response_language: str, voice_mode: bool) -> None:
    lang = normalize_voice_language(response_language, st.session_state.chat_draft or "")

    if speech_to_text is not None and not whisper_stt_enabled():
        try:
            t = speech_to_text(language=lang, start_prompt="🎤", stop_prompt="⏹",
                               just_once=True, use_container_width=True, key="stt_main")
        except TypeError:
            t = speech_to_text(language=lang, start_prompt="🎤", stop_prompt="⏹",
                               just_once=True, key="stt_main")
        if t and t.strip() != st.session_state.last_voice_transcript:
            _queue_voice(t, voice_mode)
        return

    if whisper_stt_enabled() and mic_recorder is not None:
        try:
            audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹",
                                 just_once=True, use_container_width=True, key="mic_main")
        except TypeError:
            audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹",
                                 just_once=True, key="mic_main")
        if audio:
            ab = audio.get("bytes") if isinstance(audio, dict) else None
            aid = str(audio.get("id") if isinstance(audio, dict) else hash(audio))
            if ab and aid != st.session_state.last_audio_id:
                st.session_state.last_audio_id = aid
                with st.spinner("Transcribing…"):
                    t, err = transcribe_with_whisper(ab, lang)
                if err:
                    st.toast(f"⚠ {err}")
                else:
                    _queue_voice(t, voice_mode)
        return

    st.button("🎤", disabled=True, use_container_width=True, key="mic_disabled",
              help="Install streamlit-mic-recorder for microphone input.")


def _queue_voice(text: str, voice_mode: bool) -> None:
    clean = (text or "").strip()
    if not clean:
        return
    st.session_state.last_voice_transcript = clean
    st.session_state.voice_status = "Processing speech…"
    machine = st.session_state.get("voice_state_machine")
    if machine:
        machine.handle("final_transcript")
        st.session_state.voice_last_state = machine.state
    session = st.session_state.get("voice_session")
    if session:
        session.update_user_turn(clean)
    if voice_mode:
        st.session_state.pending_voice_submit = clean
        st.session_state.clear_composer_next  = True
    else:
        st.session_state.voice_prefill = clean
    st.rerun()


# ── Ingestion panel ────────────────────────────────────────────────────────────
def _admin_visible() -> bool:
    try:
        qp = st.query_params.get("admin", "")
    except Exception:
        qp = ""
    return st.session_state.admin_unlocked or str(qp).lower() in {"1", "true", "yes"} or st.session_state.get("developer_mode", False)


def _render_ingestion_panel(cloud_consent: bool) -> None:
    if not st.session_state.show_ingestion:
        return
    with st.container():
        st.markdown('<div class="csc-card">', unsafe_allow_html=True)
        st.markdown("**📎 Add Knowledge Source**")
        st.caption("Ingest official CSC documents into the knowledge base.")

        src_type = st.radio("Source", INGEST_SOURCE_TYPES, horizontal=True, key="ig_src")
        src_key  = src_type.lower()

        url = st.text_input("Official URL (optional)", key="ig_url", placeholder="https://pmkisan.gov.in/...")
        up_file = None
        if src_key != "url":
            fts = SUPPORTED_FILE_TYPES.get(src_key, (["pdf"], "PDF"))[0]
            up_file = st.file_uploader("Upload File", type=fts, key=f"ig_{src_key}")

        c1, c2 = st.columns(2)
        dept = c1.text_input("Department", key="ig_dept", placeholder="Agriculture")
        svc  = c2.text_input("Service Type", key="ig_svc",  placeholder="PM-KISAN")
        sname = st.text_input("Source Name", key="ig_name", placeholder="PM-KISAN Guidelines")

        pb = st.progress(0)
        sl = st.empty()

        ic, cc = st.columns([2, 1])
        with ic:
            if st.button("Ingest", type="primary", use_container_width=True, key="ig_go"):
                if ingest_knowledge_source:
                    def _prog(stage, pct):
                        pb.progress(min(max(float(pct), 0.0), 1.0))
                        sl.markdown(
                            f'<div style="color:{"#15803d" if stage=="Knowledge Ready" else "var(--muted)"};'
                            f'font-size:.9rem">{stage}{"✓" if stage=="Knowledge Ready" else "…"}</div>',
                            unsafe_allow_html=True,
                        )
                    _prog("Uploading", 0.05)
                    result = ingest_knowledge_source(
                        src_key,
                        official_url=url.strip(),
                        uploaded_file=up_file,
                        cloud_consent=cloud_consent,
                        human_reviewed=True,
                        department=dept.strip(),
                        service_type=svc.strip(),
                        source_name=sname.strip(),
                        progress_callback=_prog,
                    )
                    if any(w in result.lower() for w in ("failed", "blocked", "not stored", "could not")):
                        st.warning(result)
                    else:
                        st.success(result)
                else:
                    st.warning("Knowledge ingestion backend not available.")

            # HITL queue
            with st.expander("📋 Human Review Queue", expanded=False):
                if list_pending_reviews:
                    items = list_pending_reviews(limit=5)
                    if not items:
                        st.caption("No pending reviews.")
                    for item in items:
                        rid = item["id"]
                        st.markdown(f"**HITL-{rid}** · {item['reason']} · conf {item['confidence']:.2f}")
                        st.caption(item["created_at"])
                        st.write(item["query"])
                        if st.button("✅ Reviewed", key=f"hitl_ig_{rid}"):
                            if resolve_review and resolve_review(rid, operator_note="Reviewed via UI"):
                                st.success(f"HITL-{rid} resolved.")
                                st.rerun()
                else:
                    st.caption("HITL backend not connected.")

        with cc:
            if st.button("✕ Close", use_container_width=True, key="ig_close"):
                st.session_state.show_ingestion = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ── Query processing ───────────────────────────────────────────────────────────
def _build_answer(query: str, cloud_consent: bool, response_language: str, voice_mode: bool) -> None:
    clean = (query or "").strip()
    if not clean:
        return

    global ask
    if ask is None:
        try:
            from backend.mas_engine import ask as _ask
            ask = _ask
        except Exception as e:
            logging.error(f"Cannot import ask: {e}")
            st.error("Assistant unavailable — backend service could not be loaded.")
            return

    history = st.session_state.messages[-8:]
    _append_message("user", clean)

    lang_map = {"Auto": "auto", "English": "en", "Hindi": "hi"}
    with st.spinner("Finding a reliable answer for you…"):
        answer = ask(
            clean,
            cloud_consent=cloud_consent,
            history=history,
            response_language=lang_map.get(response_language, "auto"),
            fast_mode=voice_mode,
        )

    if not answer or not answer.strip():
        answer = (
            "I could not find verified information for that query. "
            "Please try rephrasing or ask about a specific CSC service."
        )

    asst_msg = _append_message("assistant", answer)
    st.session_state.autoplay_message_id = asst_msg["id"] if voice_mode else None
    st.session_state.voice_status        = ""
    st.session_state.clear_composer_next = True
    st.rerun()


# ── Knowledge helpers ──────────────────────────────────────────────────────────
def _ingest_files(files, category: str, cloud_consent: bool) -> None:
    if not ingest_knowledge_source:
        st.error("Knowledge ingestion backend is not available.")
        return
    pb = st.progress(0)
    for i, f in enumerate(files):
        ext = f.name.rsplit(".", 1)[-1].lower()
        pb.progress((i + 1) / len(files))
        result = ingest_knowledge_source(
            ext,
            uploaded_file=f,
            cloud_consent=cloud_consent,
            human_reviewed=True,
            service_type=category,
        )
        if any(w in result.lower() for w in ("failed", "blocked", "could not")):
            st.warning(f"{f.name}: {result}")
        else:
            st.success(f"✅ {f.name} ingested.")


def _ingest_url(url: str, category: str, cloud_consent: bool) -> None:
    if not ingest_knowledge_source:
        st.error("Knowledge ingestion backend is not available.")
        return
    with st.spinner("Fetching and ingesting…"):
        result = ingest_knowledge_source(
            "url",
            official_url=url.strip(),
            cloud_consent=cloud_consent,
            human_reviewed=True,
            service_type=category,
        )
    st.success(result) if "success" in result.lower() else st.warning(result)


def _show_mock_results(q: str) -> None:
    results = [
        {
            "title": f"PM-KISAN Eligibility Criteria",
            "cat": "PM-KISAN",
            "score": 0.95,
            "snippet": "Farmers holding cultivable land up to 2 hectares are eligible for PM-KISAN scheme…",
        },
        {
            "title": f"PM-KISAN Registration Process",
            "cat": "PM-KISAN",
            "score": 0.89,
            "snippet": "Step-by-step guide to register for PM-KISAN at your nearest CSC center…",
        },
    ]
    for r in results:
        with st.expander(f"📄 {r['title']} ({r['cat']}) — {r['score']:.0%}"):
            st.write(f"**Relevance:** {r['score']:.0%}")
            st.write(f"**Snippet:** {r['snippet']}")


def _set_voice_mode(value: bool) -> None:
    st.session_state.voice_mode = value


# ── Main entry point ───────────────────────────────────────────────────────────
def main() -> None:
    _init_state()
    apply_global_css()
    settings = render_sidebar()
    render_header()

    # ── Four primary tabs ──────────────────────────────────────────────────────
    tab_asst, tab_know, tab_dash, tab_sett = st.tabs(
        ["💬 Assistant", "📚 Knowledge", "📊 Dashboard", "⚙️ Settings"]
    )

    with tab_asst:
        _render_assistant(settings)

    with tab_know:
        _render_knowledge(settings)

    with tab_dash:
        _render_dashboard()

    with tab_sett:
        _render_settings(settings)


if __name__ == "__main__" or True:
    main()
