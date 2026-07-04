import asyncio
import io
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import wave
import struct
import math

# Import from existing AI modules
from backend.voice_assistant import synthesize_with_openai, transcribe_with_whisper, VoiceSession
from backend.mas_engine import ask

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="CSC Mitra Real-Time Voice")

# Allow CORS for the frontend widget
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_rms(frame: bytes) -> float:
    count = len(frame) // 2
    if count == 0:
        return 0
    try:
        shorts = struct.unpack(f'<{count}h', frame)
        sum_squares = sum(s * s for s in shorts)
        return math.sqrt(sum_squares / count)
    except Exception:
        return 0

def is_speech(frame: bytes, sample_rate: int = 16000) -> bool:
    """Returns True if the frame contains speech based on energy threshold."""
    # A typical threshold for silence in 16-bit PCM is around 300 to 500
    rms = get_rms(frame)
    return rms > 400

@app.websocket("/ws/audio")
async def audio_websocket(websocket: WebSocket):
    await websocket.accept()
    session = VoiceSession()
    
    # Audio settings expected from client
    sample_rate = 16000
    frame_duration_ms = 30
    frame_size = int(sample_rate * (frame_duration_ms / 1000.0) * 2) # 2 bytes per sample (16-bit PCM)
    
    audio_buffer = bytearray()
    speech_frames = 0
    silence_frames = 0
    is_recording = False
    current_task = None
    
    try:
        while True:
            # We expect the client to send either JSON (for control messages) or Bytes (for audio)
            message = await websocket.receive()
            
            if "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "barge_in":
                    # Client interrupted the AI
                    logger.info("Barge-in detected!")
                    if current_task and not current_task.done():
                        current_task.cancel()
                    audio_buffer.clear()
                    is_recording = False
                    
            elif "bytes" in message:
                frame = message["bytes"]
                
                # Split incoming audio into exact VAD-compatible frames
                for i in range(0, len(frame), frame_size):
                    chunk = frame[i:i+frame_size]
                    if len(chunk) < frame_size:
                        continue # Skip partial frames at the end
                    
                    speech_active = is_speech(chunk, sample_rate)
                    
                    if speech_active:
                        is_recording = True
                        speech_frames += 1
                        silence_frames = 0
                        audio_buffer.extend(chunk)
                    else:
                        if is_recording:
                            audio_buffer.extend(chunk)
                            silence_frames += 1
                            
                            # If we hit ~1 second of silence, process the audio
                            if silence_frames > (1000 / frame_duration_ms):
                                is_recording = False
                                
                                # Process the complete utterance in the background
                                if current_task and not current_task.done():
                                    current_task.cancel()
                                current_task = asyncio.create_task(
                                    process_utterance(websocket, audio_buffer.copy(), session, sample_rate)
                                )
                                audio_buffer.clear()
                                speech_frames = 0
                                silence_frames = 0
                                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

def create_wav_buffer(pcm_data: bytes, sample_rate: int) -> bytes:
    """Wraps raw PCM data into a WAV file format expected by Whisper API."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_io.getvalue()

async def process_utterance(websocket: WebSocket, pcm_data: bytearray, session: VoiceSession, sample_rate: int):
    # Ensure minimum audio length
    if len(pcm_data) < sample_rate * 2 * 0.5: # < 0.5 seconds
        return
        
    await websocket.send_json({"type": "status", "message": "Listening finished, transcribing..."})
    
    # 1. Convert to WAV for Whisper
    wav_data = create_wav_buffer(pcm_data, sample_rate)
    
    # 2. Transcribe
    # Run in thread pool to not block asyncio event loop
    text, stt_err = await asyncio.to_thread(transcribe_with_whisper, wav_data, "Auto")
    
    if stt_err or not text:
        await websocket.send_json({"type": "error", "message": stt_err or "No speech detected"})
        return
        
    await websocket.send_json({"type": "transcript", "text": text})
    await websocket.send_json({"type": "status", "message": "Thinking..."})
    
    # 3. LLM Processing
    # Integrate with MAS Engine for query resolution
    answer = await asyncio.to_thread(ask, text, True, [], "auto", False)
    if not answer:
        answer = "I could not understand the request."
    
    await websocket.send_json({"type": "response", "text": answer})
    await websocket.send_json({"type": "status", "message": "Speaking..."})
    
    # 4. Text-to-Speech
    audio_content, tts_err = await asyncio.to_thread(synthesize_with_openai, answer, "Auto")
    
    if tts_err:
        await websocket.send_json({"type": "error", "message": tts_err})
        return
        
    # Send MP3 to client
    if audio_content:
        try:
            await websocket.send_bytes(audio_content)
            await websocket.send_json({"type": "status", "message": "Done speaking."})
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
