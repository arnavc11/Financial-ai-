from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional
import io
import os
import tempfile
import base64
from datetime import datetime

router = APIRouter()

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

_tts_engine = None

def get_tts_engine():
    global _tts_engine
    if _tts_engine is None and TTS_AVAILABLE:
        _tts_engine = pyttsx3.init()

        _tts_engine.setProperty("rate", 160)
        _tts_engine.setProperty("volume", 0.9)

        voices = _tts_engine.getProperty("voices")
        for voice in voices:
            if "india" in voice.name.lower() or "ravi" in voice.name.lower():
                _tts_engine.setProperty("voice", voice.id)
                break
    return _tts_engine

@router.get("/status")
async def voice_status():
    return {
        "speech_to_text": {
            "available": STT_AVAILABLE,
            "library": "SpeechRecognition",
            "install": "pip install SpeechRecognition pyaudio",
            "engines": ["Google (online, free)", "Whisper (offline, free)"] if STT_AVAILABLE else []
        },
        "text_to_speech": {
            "available": TTS_AVAILABLE,
            "library": "pyttsx3",
            "install": "pip install pyttsx3",
            "note": "Uses your OS built-in voice — no internet needed"
        },
        "voice_chat": {
            "available": STT_AVAILABLE and TTS_AVAILABLE,
            "description": "Full voice pipeline: speak → AI → speak back"
        }
    }

@router.post("/speech-to-text")
async def speech_to_text(
    audio: UploadFile = File(...),
    engine: str = Form("google", description="'google' (online) or 'sphinx' (offline)")
):
    if not STT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio"
        )

    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        recognizer = sr.Recognizer()

        with sr.AudioFile(tmp_path) as source:

            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            audio_data = recognizer.record(source)

        if engine == "sphinx":

            try:
                text = recognizer.recognize_sphinx(audio_data)
                engine_used = "CMU Sphinx (offline)"
            except Exception:
                raise HTTPException(status_code=500, detail="Sphinx engine failed. Try: pip install pocketsphinx")
        else:

            text = recognizer.recognize_google(audio_data, language="en-IN")
            engine_used = "Google Speech Recognition (online)"

        return {
            "text": text,
            "engine": engine_used,
            "language": "en-IN",
            "timestamp": datetime.now().isoformat()
        }

    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio. Speak clearly.")
    except sr.RequestError as e:
        raise HTTPException(status_code=503, detail=f"STT service error: {e}")
    finally:
        os.unlink(tmp_path)

@router.post("/text-to-speech")
async def text_to_speech(
    text: str = Form(..., description="Text to convert to speech"),
    return_base64: bool = Form(False, description="Return base64 instead of audio file")
):
    if not TTS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="pyttsx3 not installed. Run: pip install pyttsx3"
        )

    if len(text) > 2000:
        text = text[:2000] + "... and more."

    engine = get_tts_engine()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp_path = tmp.name

    try:
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        if return_base64:
            return {
                "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
                "format": "WAV",
                "usage": "In browser: new Audio('data:audio/wav;base64,' + audio_base64).play()"
            }
        else:
            return Response(
                content=audio_bytes,
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=arthiai_speech.wav"}
            )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.post("/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    user_id: str = Form("anonymous"),
    speak_response: bool = Form(True)
):
    if not STT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice features unavailable. Install: pip install SpeechRecognition pyaudio pyttsx3")

    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.record(source)

        try:
            user_text = recognizer.recognize_google(audio_data, language="en-IN")
        except sr.UnknownValueError:
            raise HTTPException(status_code=400, detail="Could not hear you clearly. Please try again.")
    finally:
        os.unlink(tmp_path)

    import httpx as _httpx
    from datetime import datetime as _dt

    market_ctx = "RBI Repo Rate: 6.00% | USD/INR: ~83.50"
    try:
        async with _httpx.AsyncClient(timeout=5) as c:
            r = await c.get("https://api.coingecko.com/api/v3/simple/price",
                            params={"ids": "bitcoin", "vs_currencies": "inr"})
            btc = r.json().get("bitcoin", {}).get("inr", 0)
            market_ctx += f" | Bitcoin: Rs.{btc:,.0f}"
    except Exception:
        pass

    system = (
        "You are ArthAI, an Indian financial assistant. "
        "Give SHORT, clear answers (2-3 sentences max) since this is a voice response. "
        "Use Indian Rupees (Rs.). "
        f"Current market: {market_ctx}"
    )

    ai_reply = "Sorry, AI service is not available right now. Please check if Ollama is running."
    try:
        async with _httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user_text}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.6, "num_predict": 150}
                }
            )
            ai_reply = r.json()["message"]["content"]
    except Exception as e:
        ai_reply = f"I am having trouble connecting to the AI. Error: {str(e)[:50]}"

    audio_b64 = None
    if speak_response and TTS_AVAILABLE:
        try:
            engine = get_tts_engine()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp_path = tmp.name
            engine.save_to_file(ai_reply, tmp_path)
            engine.runAndWait()
            with open(tmp_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("utf-8")
            os.unlink(tmp_path)
        except Exception:
            pass

    return {
        "user_said":      user_text,
        "ai_replied":     ai_reply,
        "audio_base64":   audio_b64,
        "audio_format":   "WAV" if audio_b64 else None,
        "audio_usage":    "new Audio('data:audio/wav;base64,' + audio_base64).play()" if audio_b64 else None,
        "timestamp":      datetime.now().isoformat(),
    }

@router.post("/parse-command")
async def parse_voice_command(text: str = Form(...)):
    text_lower = text.lower()

    result = {"original": text, "parsed": None, "confidence": "low"}

    if "watchlist" in text_lower and ("add" in text_lower or "watch" in text_lower):
        words = text.upper().split()

        for word in words:
            if word.isalpha() and 2 <= len(word) <= 15 and word not in ("ADD", "TO", "THE", "WATCHLIST"):
                result["parsed"] = {"action": "watchlist_add", "symbol": word}
                result["confidence"] = "medium"
                break

    elif "alert" in text_lower:
        import re
        symbol_match = re.search(r'\b([A-Z]{2,15})\b', text.upper())
        price_match  = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)', text.replace(",", ""))
        direction    = "above" if "above" in text_lower else ("below" if "below" in text_lower else "above")
        if symbol_match and price_match:
            result["parsed"] = {
                "action": "alert_create",
                "symbol": symbol_match.group(1),
                "alert_type": direction,
                "target_value": float(price_match.group(1).replace(",", ""))
            }
            result["confidence"] = "high"

    elif "chart" in text_lower or "graph" in text_lower:
        words = text.upper().split()
        for word in words:
            if word.isalpha() and 2 <= len(word) <= 15 and word not in ("CHART", "GRAPH", "SHOW", "THE", "ME"):
                result["parsed"] = {"action": "chart", "symbol": word}
                result["confidence"] = "medium"
                break

    elif "bitcoin" in text_lower or "crypto" in text_lower or "btc" in text_lower:
        result["parsed"] = {"action": "crypto_price", "symbol": "bitcoin"}
        result["confidence"] = "high"

    elif "nifty" in text_lower or "sensex" in text_lower:
        result["parsed"] = {
            "action": "index_quote",
            "symbol": "NIFTY50" if "nifty" in text_lower else "SENSEX"
        }
        result["confidence"] = "high"

    return result
