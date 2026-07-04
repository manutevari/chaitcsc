from backend.voice_assistant import StreamingTranscriptBuffer, VoiceSession, VoiceStateMachine


def test_voice_state_machine_transitions():
    machine = VoiceStateMachine()
    assert machine.state == "Idle"

    machine.handle("user_speaking")
    assert machine.state == "Listening"

    machine.handle("llm_started")
    assert machine.state == "Thinking"

    machine.handle("tts_started")
    assert machine.state == "Speaking"

    machine.handle("barge_in")
    assert machine.state == "Interrupted"

    machine.handle("recover")
    assert machine.state == "Recovering"

    machine.handle("resume")
    assert machine.state == "Listening"


def test_voice_session_tracks_language_and_sentiment():
    session = VoiceSession()
    session.update_user_turn("मैं बहुत frustrated हूँ और urgent help चाहिए")

    snapshot = session.snapshot()
    assert snapshot["language"] in {"hi", "en", "ta", "te", "kn", "ml", "gu", "mr", "pa", "bn", "ur", "or", "as", "ne", "kok", "mai", "brx", "sat", "doi", "ks", "mni", "sd"}
    assert snapshot["emotion"] in {"frustrated", "angry", "urgent", "neutral", "confused"}
    assert snapshot["urgency"] in {"medium", "high", "critical", "low"}
    assert snapshot["memory"]["last_intent"]


def test_streaming_transcript_buffer_emits_final_event():
    buffer = StreamingTranscriptBuffer()
    first = buffer.push_chunk("Hello")
    assert first["is_final"] is False

    final = buffer.push_chunk(" there.")
    assert final["is_final"] is True
    assert final["text"].strip() == "Hello there."
