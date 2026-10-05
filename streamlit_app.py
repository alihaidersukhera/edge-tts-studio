"""
Edge TTS Studio — Streamlit version (for free hosting on Streamlit Community Cloud).

Deploy: push this file + requirements.txt to GitHub, then create the app at
share.streamlit.io selecting this file. No credit card needed.
"""

import asyncio

import edge_tts
import streamlit as st

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

VOLUMES = {
    "Normal": "+0%",
    "Loud (+50%)": "+50%",
    "Extra loud (+100%)": "+100%",
}

MAX_CHARS = 300000


async def generate_audio(text: str, voice_id: str, volume: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice_id, volume=volume)
    parts = []
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            parts.append(chunk["data"])
    return b"".join(parts)


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
                audio = asyncio.run(
                    generate_audio(
                        text.strip(), VOICES[voice_label], VOLUMES[volume_label]
                    )
                )
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
                audio = None
        if audio:
            st.success("Done! Play it below or download the MP3.")
            st.audio(audio, format="audio/mp3")
            st.download_button(
                "⬇️ Download MP3",
                data=audio,
                file_name="speech.mp3",
                mime="audio/mpeg",
            )

st.divider()
st.caption("Powered by Microsoft Edge TTS (free) · Hosted free on Streamlit Cloud")
