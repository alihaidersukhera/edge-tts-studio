"""
Edge TTS Studio — Streamlit version (for free hosting on Streamlit Community Cloud).

Primary engine: Microsoft Edge TTS (free neural voices).
Fallback engine: Google TTS (gTTS) — used automatically when Microsoft's
endpoint refuses the connection (e.g. 403 from cloud hosts), so the app
always produces audio. Voice names stay the same; on fallback the matching
language voice is used.
"""

import asyncio
import io
import re

import edge_tts
import streamlit as st
from gtts import gTTS

st.set_page_config(page_title="Edge TTS Studio", page_icon="🔊")

VOICES = {
    "Asad — Urdu (Pakistan, Male)": "ur-PK-AsadNeural",
    "Uzma — Urdu (Pakistan, Female)": "ur-PK-UzmaNeural",
    "Gul — Urdu (India, Female)": "ur-IN-GulNeural",
    "Salman — Urdu (India, Male)": "ur-IN-SalmanNeural",
    "Swara — Hindi (India, Female)": "hi-IN-SwaraNeural",
    "Madhur — Hindi (India, Male)": "hi-IN-MadhurNeural",
    "Aria — English (US, Female)": "en-US-AriaNeural",
    "Guy — English (US, Male)": "en-US-GuyNeural",
    "Ryan — English (UK, Male)": "en-GB-RyanNeural",
}

# Fallback language per Edge voice (gTTS has one voice per language).
VOICE_LANG = {
    "ur-PK-AsadNeural": "ur",
    "ur-PK-UzmaNeural": "ur",
    "ur-IN-GulNeural": "ur",
    "ur-IN-SalmanNeural": "ur",
    "hi-IN-SwaraNeural": "hi",
    "hi-IN-MadhurNeural": "hi",
    "en-US-AriaNeural": "en",
    "en-US-GuyNeural": "en",
    "en-GB-RyanNeural": "en",
}

VOLUMES = {
    "Normal": "+0%",
    "Loud (+50%)": "+50%",
    "Extra loud (+100%)": "+100%",
}

MAX_CHARS = 300000
GTTS_CHUNK = 4000


async def generate_edge(text: str, voice_id: str, volume: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice_id, volume=volume)
    parts = []
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            parts.append(chunk["data"])
    return b"".join(parts)


def generate_gtts(text: str, lang: str) -> bytes:
    """Google TTS fallback: split into chunks, concatenate MP3 bytes."""
    chunks, cur = [], ""
    for piece in re.split(r"(?<=[.!?])\s+", text):
        if len(cur) + len(piece) + 1 > GTTS_CHUNK:
            if cur:
                chunks.append(cur)
            cur = piece
        else:
            cur = f"{cur} {piece}" if cur else piece
    if cur:
        chunks.append(cur)
    out = io.BytesIO()
    for ch in chunks:
        buf = io.BytesIO()
        gTTS(text=ch, lang=lang).write_to_fp(buf)
        out.write(buf.getvalue())
    return out.getvalue()


def generate_audio(text: str, voice_id: str, volume: str) -> tuple[bytes, str]:
    """Returns (audio_bytes, engine_name). Edge first, gTTS fallback."""
    try:
        audio = asyncio.run(generate_edge(text, voice_id, volume))
        if audio:
            return audio, "edge"
    except Exception:
        pass
    return generate_gtts(text, VOICE_LANG[voice_id]), "gtts"


st.title("🔊 Edge TTS Studio")
st.caption("Free text-to-speech — Urdu, Hindi & English voices")

text = st.text_area(
    "Your text",
    height=200,
    max_chars=MAX_CHARS,
    placeholder="Type or paste text here… (Urdu, Hindi ya English)",
)
st.caption(f"{len(text)} / {MAX_CHARS}")

voice_label = st.selectbox("Voice", list(VOICES.keys()))
volume_label = st.selectbox("Volume", list(VOLUMES.keys()), index=1)

if st.button("🎙️ Generate Audio", type="primary"):
    if not text.strip():
        st.error("Please enter some text first.")
    else:
        with st.spinner("Generating audio… (long texts take longer)"):
            try:
                audio, engine = generate_audio(
                    text.strip(), VOICES[voice_label], VOLUMES[volume_label]
                )
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
                audio, engine = None, ""
        if audio:
            st.success("Done! Play it below or download the MP3.")
            if engine == "gtts":
                st.info(
                    "Note: Microsoft ki voice abhi busy thi, is liye backup "
                    "voice (Google) use hui hai — awaz thori different hogi."
                )
            st.audio(audio, format="audio/mp3")
            st.download_button(
                "⬇️ Download MP3",
                data=audio,
                file_name="speech.mp3",
                mime="audio/mpeg",
            )

st.divider()
st.caption("Powered by Microsoft Edge TTS (free) · Hosted free on Streamlit Cloud")
