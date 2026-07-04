"""
CSC Assistant Page (modernized)
Redirects to the unified 4-tab interface; kept for Streamlit sidebar navigation compat.
"""

import streamlit as st
import sys, os

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

st.set_page_config(page_title="CSC Assistant", page_icon="💬", layout="wide")

# ── backend import ────────────────────────────────────────────────────────────
try:
    from backend.mas_engine import ask
    BACKEND_AVAILABLE = True
except ImportError:
    try:
        from mas_engine import ask
        BACKEND_AVAILABLE = True
    except ImportError:
        ask = None
        BACKEND_AVAILABLE = False

# ── design system ─────────────────────────────────────────────────────────────
from components.styles import apply_global_css
apply_global_css()

# ── session state defaults ────────────────────────────────────────────────────
for k, v in {"conversation_history": [], "assistant_prefill": ""}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="csc-hero">
  <h1>💬 CSC Assistant</h1>
  <p>Multi-agent powered assistant for CSC service discovery and workflow guidance.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── tip banner ────────────────────────────────────────────────────────────────
st.info("💡 Use the **main app** (`streamlit run streamlit_app.py`) for the full ChatGPT-style experience with voice, dashboard, and knowledge management.")

# ── quick prompts ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-hdr">Quick Prompts</div>', unsafe_allow_html=True)
qps = [
    "PM Kisan registration process",
    "PAN card correction steps",
    "e-Shram registration requirements",
    "DigiPay cash withdrawal guide",
]
cols = st.columns(4)
for i, p in enumerate(qps):
    if cols[i].button(p, use_container_width=True, key=f"qp_page_{i}"):
        st.session_state.assistant_prefill = p

# ── voice component (inline WebSocket) ───────────────────────────────────────
import streamlit.components.v1 as components, base64

VOICE_HTML = """<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  body{margin:0;padding:0;font-family:'Inter',sans-serif;background:transparent}
  .vc{background:linear-gradient(145deg,#fff,#f8fafc);border:1px solid #e2e8f0;border-radius:14px;
      padding:20px;box-shadow:0 8px 20px rgba(0,0,0,.06);display:flex;flex-direction:column;align-items:center}
  .controls{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;justify-content:center}
  .btn{border:none;padding:9px 18px;font-size:13px;font-weight:600;border-radius:9999px;cursor:pointer;
       display:flex;align-items:center;gap:5px;transition:all .25s}
  .btn:disabled{opacity:.4;cursor:not-allowed}
  .btn-p{background:linear-gradient(135deg,#0ea5e9,#2563eb);color:#fff;box-shadow:0 3px 10px rgba(37,99,235,.35)}
  .btn-p:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 5px 16px rgba(37,99,235,.4)}
  .btn-s{background:#fff;color:#4b5563;border:1px solid #d1d5db}
  .btn-d{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff}
  .sc{display:flex;align-items:center;gap:6px;background:#f1f5f9;padding:6px 12px;border-radius:9999px;
      font-size:12px;color:#475569;font-weight:500;margin-bottom:12px;border:1px solid #e2e8f0}
  .pd{height:8px;width:8px;background:#94a3b8;border-radius:50%;display:inline-block}
  .is-l .pd{background:#ef4444;animation:pr 1.5s infinite}
  .is-a .pd{background:#22c55e;animation:pg 1.5s infinite}
  @keyframes pg{0%{box-shadow:0 0 0 0 rgba(34,197,94,.7)}70%{box-shadow:0 0 0 6px rgba(34,197,94,0)}100%{box-shadow:0 0 0 0 rgba(34,197,94,0)}}
  @keyframes pr{0%{box-shadow:0 0 0 0 rgba(239,68,68,.7)}70%{box-shadow:0 0 0 8px rgba(239,68,68,0)}100%{box-shadow:0 0 0 0 rgba(239,68,68,0)}}
  .tb{width:100%;background:#fff;border-radius:10px;padding:12px;min-height:70px;max-height:120px;
      overflow-y:auto;border:1px solid #e5e7eb;box-sizing:border-box;display:flex;flex-direction:column;gap:5px}
  .m{font-size:13px;line-height:1.5}
  .my{color:#64748b}.ma{color:#0f172a;font-weight:500}
  .me{color:#ef4444;background:#fef2f2;padding:8px;border-radius:6px;border:1px solid #fecaca}
</style></head><body>
<div class="vc">
  <div class="controls">
    <button id="sB" class="btn btn-p">🎤 Start Voice</button>
    <button id="stB" class="btn btn-s" disabled>⏹ Stop</button>
    <button id="bI" class="btn btn-d" disabled>✕ Interrupt</button>
  </div>
  <div id="sc" class="sc"><span id="pd" class="pd"></span><span id="st">Disconnected</span></div>
  <div id="tb" class="tb"><div class="m my" style="text-align:center">Ready · Press Start Voice</div></div>
</div>
<script>
let ws=null,ac=null,ms=null,proc=null;
const sB=document.getElementById('sB'),stB=document.getElementById('stB'),
      bI=document.getElementById('bI'),sSt=document.getElementById('st'),
      tb=document.getElementById('tb'),sc=document.getElementById('sc');
function addMsg(t,tp){if(tb.innerHTML.includes('Ready'))tb.innerHTML='';
  if(tp==='e')tb.innerHTML=`<div class="m me">${t}</div>`;
  else if(tp==='y')tb.innerHTML+=`<div class="m my"><b>You:</b> ${t}</div>`;
  else tb.innerHTML+=`<div class="m ma"><b>AI:</b> ${t}</div>`;
  tb.scrollTop=tb.scrollHeight;}
function setSt(t,c){sSt.innerText=t;sc.className='sc '+(c||'');}
sB.onclick=async()=>{try{
  ws=new WebSocket('ws://localhost:8000/ws/audio');
  ws.onopen=()=>{setSt('Listening…','is-l');sB.disabled=true;stB.disabled=false;bI.disabled=false;rec();};
  ws.onmessage=async(e)=>{if(typeof e.data==='string'){let d=JSON.parse(e.data);
    if(d.type==='status'){if(d.message.includes('Speaking'))setSt(d.message,'is-a');else setSt(d.message,'is-l');}
    else if(d.type==='transcript')addMsg(d.text,'y');
    else if(d.type==='response')addMsg(d.text,'a');
    else if(d.type==='error')addMsg(d.message,'e');
  }else play(e.data);};
  ws.onclose=()=>{setSt('Disconnected','');sB.disabled=false;stB.disabled=true;bI.disabled=true;stop();};
}catch(ex){setSt('Error','');addMsg('Could not connect','e');}};
stB.onclick=()=>{if(ws)ws.close();};
bI.onclick=()=>{if(ws&&ws.readyState===1){ws.send(JSON.stringify({type:'barge_in'}));setSt('Interrupted','is-l');}};
async function rec(){ms=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
  ac=new(window.AudioContext||window.webkitAudioContext)({sampleRate:16000});
  const src=ac.createMediaStreamSource(ms);proc=ac.createScriptProcessor(4096,1,1);
  proc.onaudioprocess=(e)=>{if(!ws||ws.readyState!==1)return;
    const inp=e.inputBuffer.getChannelData(0),pcm=new Int16Array(inp.length);
    for(let i=0;i<inp.length;i++){let s=Math.max(-1,Math.min(1,inp[i]));pcm[i]=s<0?s*0x8000:s*0x7FFF;}
    ws.send(pcm.buffer);};
  src.connect(proc);proc.connect(ac.destination);}
function stop(){if(proc){proc.disconnect();proc=null;}if(ms){ms.getTracks().forEach(t=>t.stop());ms=null;}if(ac){ac.close();ac=null;}}
async function play(d){try{if(!ac)ac=new(window.AudioContext||window.webkitAudioContext)();
  if(ac.state==='suspended')await ac.resume();
  const b=await new Blob([d]).arrayBuffer();const a=await ac.decodeAudioData(b);
  const s=ac.createBufferSource();s.buffer=a;s.connect(ac.destination);s.start(0);
}catch(ex){try{const b=new Blob([d],{type:'audio/mpeg'});await new Audio(URL.createObjectURL(b)).play();}catch(e){addMsg('Speaker blocked','e');}}}
</script></body></html>"""

with st.expander("🎙️ Real-Time Voice Assistant", expanded=False):
    components.iframe(
        "data:text/html;base64," + base64.b64encode(VOICE_HTML.encode()).decode(),
        height=300,
    )

# ── text chat ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-hdr">💬 Ask Your Question</div>', unsafe_allow_html=True)

def _validate(q):
    q = q.strip()
    if not q: return False, "⚠️ Please enter a question."
    if len(q) < 5: return False, "⚠️ Query too short (min 5 chars)."
    if len(q) > 1000: return False, "⚠️ Query too long (max 1000 chars)."
    if q.replace(" ", "").isnumeric(): return False, "⚠️ Please ask a meaningful question."
    return True, ""

query = st.text_area(
    "Your question:",
    value=st.session_state.assistant_prefill,
    placeholder="Ask about any CSC service or scheme…",
    height=100,
    key="page_query_area",
)
st.session_state.assistant_prefill = ""

submit = st.button("🚀 Get Answer", type="primary", key="page_submit")

if submit:
    valid, err = _validate(query or "")
    if not valid:
        st.error(err)
    elif not BACKEND_AVAILABLE:
        st.error("⚠️ Backend unavailable. Run `streamlit run streamlit_app.py` for the full experience.")
    else:
        history = []
        for q_t, a_t in st.session_state.conversation_history[-4:]:
            history += [{"role": "user", "content": q_t}, {"role": "assistant", "content": a_t}]
        cloud = st.session_state.get("cloud_consent", True)
        lang  = {"Auto": "auto", "English": "en", "Hindi": "hi"}.get(
            st.session_state.get("response_language", "Auto"), "auto"
        )
        with st.spinner("Processing with multi-agent architecture…"):
            try:
                answer = ask(query.strip(), cloud_consent=cloud, history=history,
                             response_language=lang, fast_mode=False)
                if not answer or not answer.strip():
                    answer = "I could not find verified information. Please rephrase or ask about a specific CSC service."
            except Exception as exc:
                st.error(f"❌ Error: {exc}")
                answer = None
        if answer:
            st.markdown(
                f'<div class="csc-card" style="border-left:3px solid var(--primary)">{answer}</div>',
                unsafe_allow_html=True,
            )
            st.session_state.conversation_history.append((query.strip(), answer))

# ── history ───────────────────────────────────────────────────────────────────
if st.session_state.conversation_history:
    st.markdown('<div class="section-hdr">📜 Conversation History</div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear", key="clear_hist_page"):
        st.session_state.conversation_history = []
        st.rerun()
    for i, (q_t, a_t) in enumerate(reversed(st.session_state.conversation_history)):
        label = f"Q{len(st.session_state.conversation_history)-i}: {q_t[:60]}{'…' if len(q_t)>60 else ''}"
        with st.expander(label, expanded=(i == 0)):
            st.markdown(f"**Q:** {q_t}")
            st.markdown(f"**A:** {a_t}")
