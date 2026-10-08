# Task 4: Voice Synthesis App 🎙️

A Streamlit web application that converts text to speech using the ElevenLabs API. It dynamically fetches available voices associated with your ElevenLabs account and synthesizes speech using the `eleven_multilingual_v2` model.

## 🚀 Features

- **Dynamic Voice Selection**: Fetches available voices directly from your ElevenLabs account via `client.voices.get_all()`.
- **Text-to-Speech Synthesis**: Converts custom user text into natural-sounding audio.
- **Audio Playback**: Integrated Streamlit audio player for instant playback.

## 🛠️ Requirements

- Python 3.10+
- `streamlit`
- `elevenlabs`

## ⚙️ Setup & Execution

1. Navigate to the `Task_4_Voice_Cloner` directory:
   ```bash
   cd Task_4_Voice_Cloner
