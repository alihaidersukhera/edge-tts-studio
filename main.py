"""
Edge-TTS Web App — FastAPI backend.

Serves the frontend (index.html) and exposes a JSON API that converts
text to MP3 audio using Microsoft Edge voices via the `edge-tts` library.

Run:
    uvicorn main:app --host 127.0.0.1 --port 8000
Then open: http://127.0.0.1:8000
"""

import os

import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="Edge TTS Web App")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# key -> Microsoft Edge TTS voice id (+ human label for the dropdown)
VOICES = {
    "asad":    {"id": "ur-PK-AsadNeural",  "label": "Asad — Urdu (Pakistan, Male)"},
    "uzma":    {"id": "ur-PK-UzmaNeural",  "label": "Uzma — Urdu (Pakistan, Female)"},
    "hindi":   {"id": "hi-IN-SwaraNeural", "label": "Swara — Hindi (India, Female)"},
    "english": {"id": "en-US-AriaNeural",  "label": "Aria — English (US, Female)"},
}

MAX_CHARS = 10000


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_CHARS)
    voice: str = "asad"
    volume: Literal["+0%", "+50%", "+100%"] = "+50%"


@app.get("/", include_in_schema=False)
async def home():
    """Serve the frontend page."""
    index_path = os.path.join(BASE_DIR, "index.html")
    if not os.path.isfile(index_path):
        return HTMLResponse(
            "<h2>index.html not found</h2>"
            "<p>Please save <code>index.html</code> in the same folder as "
            f"<code>main.py</code>:<br><code>{BASE_DIR}</code></p>",
            status_code=500,
        )
    return FileResponse(index_path)


@app.get("/api/voices")
async def list_voices():
    """Return the available voices for the dropdown."""
    return [{"key": k, "label": v["label"]} for k, v in VOICES.items()]


@app.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    """
    Generate MP3 audio for the given text + voice.
    Returns the raw MP3 bytes (audio/mpeg) so the browser can play
    and download it directly.
    """
    voice = VOICES.get(req.voice)
    if voice is None:
        raise HTTPException(status_code=400, detail=f"Unknown voice: {req.voice!r}")

    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is empty.")

    try:
        communicate = edge_tts.Communicate(text, voice["id"], volume=req.volume)
        parts = []
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                parts.append(chunk["data"])
        audio = b"".join(parts)
    except Exception as exc:  # e.g. no internet / Microsoft endpoint unreachable
        raise HTTPException(
            status_code=502, detail=f"Speech generation failed: {exc}"
        ) from exc

    if not audio:
        raise HTTPException(status_code=502, detail="No audio was generated.")

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="speech.mp3"'},
    )
