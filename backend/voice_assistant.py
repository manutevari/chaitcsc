import io
import re
import time
from typing import Any, Dict, List, Optional

import streamlit as st
from openai import OpenAI

from .env_config import get_secret as secret, get_configured_secret as configured_secret
from .sentiment_engine import SentimentEngine


DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")
HINGLISH_HINT_PATTERN = re.compile(
    r"\b("
    r"kya|kaise|batao|bataiye|karo|karna|karun|hoga|hai|nahi|"
    r"yojana|kisan|panjikaran|sudhar|praman|seva|aavedan|"
    r"process|registration|status"
    r")\b",
    re.IGNORECASE,
)

LANGUAGE_HINTS = {
    "hi": ["हिंदी", "हिन्दी", "कृपया", "क्या", "कैसे", "मदद", "सरकार"],
    "ta": ["தமிழ்", "என்ன", "உதவி", "சிக்கல்"],
    "te": ["తెలుగు", "సహాయం", "సమస్య", "ఏమిటి"],
    "kn": ["ಕನ್ನಡ", "ಸಹಾಯ", "ಸಮಸ್ಯ"],
    "ml": ["മലയാളം", "സഹായം", "പ്രശ്നം"],
    "gu": ["ગુજરાતી", "મદદ", "સમस्या"],
    "mr": ["मराठी", "मदत", "समस्या"],
    "pa": ["ਪੰਜਾਬੀ", "ਮਦਦ", "ਸਮੱਸਿਆ"],
    "bn": ["বাংলা", "সাহায্য", "সমস্যা"],
    "ur": ["اردو", "مدد", "مسئلہ"],
    "or": ["ଓଡ଼ିଆ", "ସହାୟତା", "ସମସ୍ୟା"],
    "as": ["অসমীয়া", "সহায়", "সমস্যা"],
    "ne": ["नेपाली", "मद्दत", "समस्या"],
    "kok": ["कोंकणी", "मदत", "समस्या"],
    "mai": ["मैथिली", "मदद", "समस्या"],
    "brx": ["बोड़ो", "मदद", "समस्या"],
    "sat": ["संताली", "मदद", "समस्या"],
    "doi": ["डोगरी", "मदद", "समस्या"],
    "ks": ["कश्मीरी", "मदद", "समस्या"],
    "mni": ["মণিপুরি", "সাহায্য", "সমস্যা"],
    "sd": ["سنڌي", "مدد", "مسئلہ"],
}

_SENTIMENT_ENGINE = SentimentEngine()


class VoiceStateMachine:
    """Minimal state machine for streaming voice interactions with UI status."""

    # UI status placeholder is created lazily on first UI call to avoid
    # emitting Streamlit elements when this module is imported outside
    # of a Streamlit session.
    _status_placeholder = None

    def __init__(self):
        self.state = "Idle"
        self.history: List[str] = []
        self.interruptions = 0
        self.cancellations = 0

    @staticmethod
    def _ensure_placeholder():
        if VoiceStateMachine._status_placeholder is None:
            try:
                VoiceStateMachine._status_placeholder = st.empty()
            except Exception:
                VoiceStateMachine._status_placeholder = None

    @staticmethod
    def show_status(state: str):
        """Update UI with current voice state if Streamlit is available."""
        VoiceStateMachine._ensure_placeholder()
        p = VoiceStateMachine._status_placeholder
        if p is None:
            return
        if state == "Listening":
            p.markdown("🎙️ **Listening… आप बोल रहे हैं…**")
        elif state == "Thinking":
            p.markdown("⏳ **Analyzing voice…**")
        elif state == "Speaking":
            p.markdown("🔊 **Speaking…**")
        elif state == "Interrupted":
            p.markdown("⚠️ **Interrupted…**")
        elif state == "Recovering":
            p.markdown("🔄 **Recovering…**")
        else:
            p.markdown("🟢 **Idle**")

    def handle(self, event: str) -> str:
        transitions = {
            ("Idle", "user_speaking"): "Listening",
            ("Listening", "partial_transcript"): "Listening",
            ("Listening", "final_transcript"): "Thinking",
            ("Listening", "llm_started"): "Thinking",
            ("Thinking", "tts_started"): "Speaking",
            ("Thinking", "barge_in"): "Interrupted",
            ("Speaking", "barge_in"): "Interrupted",
            ("Interrupted", "recover"): "Recovering",
            ("Interrupted", "resume"): "Listening",
            ("Recovering", "resume"): "Listening",
            ("Recovering", "llm_started"): "Thinking",
            ("Speaking", "resume"): "Listening",
            ("Listening", "recover"): "Recovering",
        }
        new_state = transitions.get((self.state, event), self.state)
        if event == "barge_in":
            self.interruptions += 1
            self.cancellations += 1
        if event in {"recover", "resume"}:
            self.history.append(event)
        self.state = new_state
        self.history.append(f"{self.state}:{event}")

        # Update UI status if available
        try:
            VoiceStateMachine.show_status(self.state)
        except Exception:
            pass

        return self.state


class StreamingTranscriptBuffer:
    """Tracks partial and final transcript fragments in a low-latency manner."""

    def __init__(self):
        self._buffer = ""

    def push_chunk(self, chunk: str) -> Dict[str, Any]:
        if chunk is None:
            chunk = ""
        self._buffer += str(chunk)
        text = self._buffer.strip()
        if not text:
            return {"text": "", "is_final": False, "partial": ""}

        is_final = bool(re.search(r"[.!?。…]$", text)) or len(text) >= 32
        return {"text": text, "is_final": is_final, "partial": text if not is_final else ""}

    def reset(self) -> None:
        self._buffer = ""


class VoiceSession:
    """Keeps multilingual conversation memory without persisting personal data."""

    def __init__(self):
        self.language = "en"
        self.emotion = "neutral"
        self.urgency = "low"
        self.context: List[str] = []
        self.last_intent = "general"
        self.last_entities: List[str] = []
        self.conversation_summary = ""
        self.turns: List[Dict[str, Any]] = []
        self.sentiment_engine = _SENTIMENT_ENGINE

    def _sanitize_text(self, text: str) -> str:
        sanitized = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[redacted]", text or "", flags=re.IGNORECASE)
        sanitized = re.sub(r"\b\d{4,}\b", "[redacted]", sanitized)
        return sanitized

    def update_user_turn(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cleaned = self._sanitize_text(text or "")
        self.language = detect_language_code(cleaned)
        profile = self.sentiment_engine.analyze_voice(cleaned, metadata=metadata or {})
        self.emotion = profile.get("emotion", "neutral")
        self.urgency = profile.get("urgency", "low")
        self.last_intent = self._infer_intent(cleaned)
        self.last_entities = self._infer_entities(cleaned)
        self.context.append(cleaned[:180])
        self.context = self.context[-6:]
        self.turns.append({"language": self.language, "text": cleaned[:240], "emotion": self.emotion, "urgency": self.urgency})
        self.conversation_summary = self._summarize_turns()
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
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

    def _infer_intent(self, text: str) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ["registration", "register", "पंजीकरण", "रजिस्टर"]):
            return "registration"
        if any(token in lowered for token in ["document", "documents", "दस्तावेज", "प्रमाण"]):
            return "documents"
        if any(token in lowered for token in ["grievance", "complaint", "problem", "शिकायत", "समस्या"]):
            return "grievance"
        if any(token in lowered for token in ["status", "track", "स्थिति", "जानकारी"]):
            return "status"
        if any(token in lowered for token in ["eligibility", "eligible", "योग्यता", "पात्र"]):
            return "eligibility"
        return "general"

    def _infer_entities(self, text: str) -> List[str]:
        tokens = re.findall(r"[A-Za-z]{3,}|[\u0900-\u097F]+", text)
        return [token for token in tokens if len(token) > 2][:6]

    def _summarize_turns(self) -> str:
        if not self.turns:
            return ""
        recent = self.turns[-3:]
        parts = []
        for turn in recent:
            parts.append(f"{turn['language']}:{turn['emotion']}:{turn['urgency']}:{turn['text']}")
        return " | ".join(parts)


def detect_language_code(text: str, fallback: str = "en") -> str:
    lowered = (text or "").lower()
    for code, hints in LANGUAGE_HINTS.items():
        if any(hint.lower() in lowered for hint in hints):
            return code
    if DEVANAGARI_PATTERN.search(text or "") or HINGLISH_HINT_PATTERN.search(text or ""):
        return "hi"
    return fallback


def normalize_voice_language(language_choice="Auto", sample_text=""):
    if language_choice in {"Hindi", "hi", "hi-IN"}:
        return "hi-IN"
    if language_choice in {"English", "en", "en-IN"}:
        return "en-IN"
    if isinstance(language_choice, str) and language_choice.lower() in {"auto", ""}:
        code = detect_language_code(sample_text or "")
        mapping = {
            "hi": "hi-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "kn": "kn-IN",
            "ml": "ml-IN",
            "gu": "gu-IN",
            "mr": "mr-IN",
            "pa": "pa-IN",
            "bn": "bn-IN",
            "ur": "ur-IN",
            "or": "or-IN",
            "as": "as-IN",
            "ne": "ne-IN",
            "kok": "kok-IN",
            "mai": "mai-IN",
            "brx": "brx-IN",
            "sat": "sat-IN",
            "doi": "doi-IN",
            "ks": "ks-IN",
            "mni": "mni-IN",
            "sd": "sd-IN",
        }
        return mapping.get(code, "en-IN")
    return "en-IN"


def openai_audio_enabled():
    return bool(configured_secret("OPENAI_AUDIO_API_KEY", "OPENAI_API_KEY"))


def voice_stt_provider():
    return secret("VOICE_STT_PROVIDER", "browser").strip().lower()


def whisper_stt_enabled():
    return voice_stt_provider() in {"openai", "whisper"} and openai_audio_enabled()


def transcribe_with_whisper(audio_bytes, language_choice="Auto"):
    if not audio_bytes:
        return "", "No audio was captured. Please try again."

    api_key = configured_secret("OPENAI_AUDIO_API_KEY", "OPENAI_API_KEY")
    if not api_key:
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                audio = recognizer.record(source)
            lang_code = "en-IN"
            if language_choice in {"Hindi", "hi", "hi-IN"}:
                lang_code = "hi-IN"
            text = recognizer.recognize_google(audio, language=lang_code)
            return text, ""
        except sr.UnknownValueError:
            return "", "Could not understand audio. Please try speaking clearer or closer to the microphone."
        except sr.RequestError as e:
            return "", f"Speech recognition service unavailable: {e}"
        except Exception as e:
            return "", f"OpenAI audio transcription is not configured, and free fallback failed: {str(e)}"

    client = OpenAI(api_key=api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "csc_voice_input.wav"

    kwargs = {
        "model": secret("OPENAI_STT_MODEL", "whisper-1"),
        "file": audio_file,
        "prompt": "CSC services, Digital Seva, PM Kisan, PAN, DigiPay, Ayushman Bharat, e-Shram, Hindi and English. Support Indian languages.",
    }

    if language_choice in {"Hindi", "hi", "hi-IN"}:
        kwargs["language"] = "hi"
    elif language_choice in {"English", "en", "en-IN"}:
        kwargs["language"] = "en"

    try:
        response = client.audio.transcriptions.create(**kwargs)
    except Exception as exc:
        error_name = exc.__class__.__name__
        if "RateLimit" in error_name:
            return "", "Voice transcription is temporarily busy. Please try again in a moment, or use browser speech input."
        return "", "Voice transcription could not complete. Please try again or type your question."

    text = getattr(response, "text", "") or ""
    return text.strip(), ""


VALID_OPENAI_VOICES = {"alloy", "echo", "fable", "nova", "onyx", "shimmer"}
VALID_OPENAI_TTS_MODELS = {"tts-1", "tts-1-hd"}


def _safe_voice(preferred, fallback="nova"):
    """Return preferred voice if valid, otherwise fallback."""
    v = (preferred or fallback).strip().lower()
    return v if v in VALID_OPENAI_VOICES else fallback


def _safe_model(preferred, fallback="tts-1"):
    """Return preferred model if valid, otherwise fallback."""
    m = (preferred or fallback).strip().lower()
    return m if m in VALID_OPENAI_TTS_MODELS else fallback


def synthesize_with_openai(text, language_choice="Auto"):
    clean_text = (text or "").strip()
    if not clean_text:
        return None, "There is no answer text to speak."

    api_key = configured_secret("OPENAI_AUDIO_API_KEY", "OPENAI_API_KEY")
    if not api_key:
        # OpenAI key not provided — try a better local fallback (edge-tts) first,
        # then fall back to gTTS if edge-tts isn't available.
        try:
            import asyncio
            import tempfile
            import os
            from edge_tts import Communicate

            # Choose a simple voice mapping based on language choice. If this
            # voice isn't supported, edge-tts will raise and we'll fallback.
            if language_choice in {"Hindi", "hi", "hi-IN"}:
                voice = "hi-IN-SwaraNeural"
            else:
                voice = "en-US-JennyNeural"

            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp_path = tmp.name
            tmp.close()

            async def _save():
                communicate = Communicate(clean_text[:4000], voice)
                await communicate.save(tmp_path)

            asyncio.run(_save())
            with open(tmp_path, "rb") as fh:
                data = fh.read()
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            return data, ""
        except Exception:
            # edge-tts not available or failed — try gTTS as a last resort.
            try:
                from gtts import gTTS
                lang_code = "en"
                if language_choice in {"Hindi", "hi", "hi-IN"}:
                    lang_code = "hi"
                tts = gTTS(text=clean_text[:4000], lang=lang_code, slow=False)
                mp3_fp = io.BytesIO()
                tts.write_to_fp(mp3_fp)
                return mp3_fp.getvalue(), ""
            except Exception as e:
                return None, f"OpenAI API key missing, and free TTS fallbacks (edge-tts, gTTS) failed: {e}"

    client = OpenAI(api_key=api_key)

    # Resolve voice + model based on user UI selection.
    # All voices are validated against OpenAI's supported list to prevent 400 errors.
    try:
        ui_choice = st.session_state.get("tts_voice_choice", "").lower()
    except Exception:
        ui_choice = ""

    if ui_choice == "bhashini (default)":
        voice = _safe_voice(secret("BHASHINI_VOICE", secret("OPENAI_TTS_VOICE", "nova")))
        model = _safe_model(secret("BHASHINI_TTS_MODEL", secret("OPENAI_TTS_MODEL", "tts-1")))
    elif ui_choice == "openai nova":
        voice = _safe_voice(secret("OPENAI_TTS_VOICE", "nova"))
        model = _safe_model(secret("OPENAI_TTS_MODEL", "tts-1"))
    elif ui_choice == "gemini-like (neural)":
        voice = _safe_voice(secret("GEMINI_TTS_VOICE", "alloy"))
        model = _safe_model(secret("OPENAI_TTS_MODEL", "tts-1"))
    elif ui_choice == "microsoft copilot (neural)":
        # "copilot" is not a valid OpenAI voice — map to closest valid alternative
        voice = _safe_voice(secret("MS_TTS_VOICE", "onyx"))
        model = _safe_model(secret("OPENAI_TTS_MODEL", "tts-1"))
    else:
        voice = _safe_voice(secret("OPENAI_TTS_VOICE", "nova"))
        model = _safe_model(secret("OPENAI_TTS_MODEL", "tts-1"))

    try:
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=clean_text[:4000],
            response_format="mp3",
        )
    except Exception as exc:
        error_name = exc.__class__.__name__
        error_msg = str(exc)
        if "RateLimit" in error_name:
            return None, "Voice service busy. Please try again in a few seconds."
        if "AuthenticationError" in error_name or "401" in error_msg:
            return None, "OpenAI API key is invalid or expired. Please check your OPENAI_API_KEY."
        if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            return None, "OpenAI quota exceeded. Please check your billing at platform.openai.com."
        if "model" in error_msg.lower() or "voice" in error_msg.lower():
            return None, f"TTS config error (voice='{voice}', model='{model}'): {error_msg[:120]}"
        return None, f"Voice playback failed: {error_msg[:150]}"

    if hasattr(response, "read"):
        return response.read(), ""
    if hasattr(response, "content"):
        return response.content, ""

    try:
        return bytes(response), ""
    except TypeError:
        return None, "Text-to-speech returned an unsupported audio response."


# Backwards-compatible helpers expected by older UI code
def analyze_voice_turn(text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compatibility wrapper: analyze a single user turn and return a snapshot-like dict."""
    session = VoiceSession()
    return session.update_user_turn(text or "", metadata=metadata or {})


def create_voice_session() -> VoiceSession:
    """Factory helper used by the UI to create a fresh `VoiceSession`."""
    return VoiceSession()