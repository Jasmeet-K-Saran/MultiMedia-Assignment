import streamlit as st
from elevenlabs.client import ElevenLabs

st.set_page_config(page_title="Task 4: Voice Synthesis", page_icon="🎙️", layout="wide")

st.title("Task 4: Voice Synthesis (Default Voices)")

# Sidebar API Key configuration
api_key = st.sidebar.text_input("ElevenLabs API Key", type="password")

if api_key:
    client = ElevenLabs(api_key=api_key)

    try:
        # Fetch voices available on your free tier account
        response = client.voices.get_all()
        voices = response.voices

        if voices:
            voice_options = {f"{v.name} ({v.category})": v.voice_id for v in voices}
            selected_voice = st.selectbox("Select an Available Voice", list(voice_options.keys()))
            voice_id = voice_options[selected_voice]

            text_input = st.text_area("Enter text to synthesize:", "Hello! This is speech generated using ElevenLabs default voices.")

            if st.button("Generate Speech"):
                if text_input.strip():
                    with st.spinner("Generating audio..."):
                        try:
                            audio_generator = client.text_to_speech.convert(
                                text=text_input,
                                voice_id=voice_id,
                                model_id="eleven_multilingual_v2"
                            )
                            audio_bytes = b"".join(list(audio_generator))
                            st.audio(audio_bytes, format="audio/mp3")
                            st.success("Audio generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating speech: {e}")
                else:
                    st.warning("Please enter some text.")
        else:
            st.error("No voices found for this API key.")

    except Exception as e:
        st.error(f"Error connecting to ElevenLabs API: {e}")
else:
    st.warning("Please enter your ElevenLabs API Key in the sidebar.")
