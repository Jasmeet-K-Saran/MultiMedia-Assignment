import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Task 4: Voice Cloning & Synthesis",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ Task 4: Voice Cloning & Audio Synthesis")
st.write("Clone a target voice using short sample audio and generate synthesized speech.")

# Sidebar API Key Configuration
st.sidebar.header("🔑 API Configuration")
api_key = st.sidebar.text_input(
    "ElevenLabs API Key",
    value=os.getenv("ELEVENLABS_API_KEY", ""),
    type="password",
    help="Get your key from https://elevenlabs.io"
)

if not api_key:
    st.warning("⚠️ Please enter your ElevenLabs API Key in the sidebar or set `ELEVENLABS_API_KEY` in your `.env` file.")
    st.stop()

# Initialize Client
client = ElevenLabs(api_key=api_key)

st.header("1. Upload Sample Audio & Clone Voice")
col1, col2 = st.columns([1, 1])

with col1:
    voice_name = st.text_input("Voice Name", value="My Cloned Voice")
    voice_desc = st.text_area("Voice Description (Optional)", value="Voice clone generated for Multimedia Assignment Task 4.")
    
    uploaded_files = st.file_uploader(
        "Upload Reference Audio Samples (MP3 / WAV)",
        type=["mp3", "wav", "m4a"],
        accept_multiple_files=True
    )

cloned_voice_id = st.session_state.get("cloned_voice_id", None)

with col2:
    if st.button("🚀 Clone Voice", use_container_width=True):
        if not uploaded_files:
            st.error("Please upload at least one audio sample file.")
        else:
            with st.spinner("Cloning voice via ElevenLabs API..."):
                temp_paths = []
                try:
                    for uploaded_file in uploaded_files:
                        suffix = os.path.splitext(uploaded_file.name)[1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(uploaded_file.read())
                            temp_paths.append(tmp.name)

                    voice = client.voices.ivc.create(
                        name=voice_name,
                        description=voice_desc,
                        files=temp_paths
                    )

                    st.session_state["cloned_voice_id"] = voice.voice_id
                    st.success(f"✅ Voice cloned successfully! Voice ID: `{voice.voice_id}`")
                except Exception as e:
                    st.error(f"Error cloning voice: {str(e)}")
                finally:
                    for path in temp_paths:
                        if os.path.exists(path):
                            os.remove(path)

st.divider()

st.header("2. Generate Speech with Cloned Voice")

if cloned_voice_id:
    text_input = st.text_area(
        "Enter text to generate speech:",
        value="Hello! This is a test demonstration of Task 4 voice cloning using ElevenLabs AI."
    )

    if st.button("🔊 Generate Audio", use_container_width=True):
        if not text_input.strip():
            st.error("Please enter text to synthesize.")
        else:
            with st.spinner("Synthesizing audio..."):
                try:
                    audio_stream = client.text_to_speech.convert(
                        text=text_input,
                        voice_id=cloned_voice_id,
                        model_id="eleven_multilingual_v2"
                    )

                    audio_bytes = b"".join(chunk for chunk in audio_stream if isinstance(chunk, bytes))

                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="⬇️ Download Generated Audio",
                        data=audio_bytes,
                        file_name="cloned_output.mp3",
                        mime="audio/mp3"
                    )
                except Exception as e:
                    st.error(f"Error generating audio: {str(e)}")
else:
    st.info("👈 Upload reference samples and click 'Clone Voice' above to begin synthesizing text.")
