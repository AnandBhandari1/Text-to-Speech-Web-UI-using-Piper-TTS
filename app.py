import streamlit as st
import tempfile
import os
import subprocess
from pathlib import Path
import time
import re
import random
import wave
import io

# Voice configurations
VOICE_CONFIGS = [
    {
        "id": "en_US-hfc_female-medium",
        "name": "HFC Female (Medium)",
        "file": "en_US-hfc_female-medium.onnx",
        "quality": "medium",
        "gender": "female"
    },
    {
        "id": "en_US-ljspeech-high",
        "name": "LJSpeech (High)",
        "file": "en_US-ljspeech-high.onnx",
        "quality": "high",
        "gender": "female"
    },
    {
        "id": "en_GB-cori-high",
        "name": "Cori (High)",
        "file": "en_GB-cori-high.onnx",
        "quality": "high",
        "gender": "female"
    },
    {
        "id": "en_US-amy-medium",
        "name": "Amy (Medium)",
        "file": "en_US-amy-medium.onnx",
        "quality": "medium",
        "gender": "female"
    },
    {
        "id": "en_US-bryce-medium",
        "name": "Bryce (Medium)",
        "file": "en_US-bryce-medium.onnx",
        "quality": "medium",
        "gender": "male"
    },
    {
        "id": "en_US-danny-low",
        "name": "Danny (Low)",
        "file": "en_US-danny-low.onnx",
        "quality": "low",
        "gender": "male"
    },
    {
        "id": "en_US-hfc_male-medium",
        "name": "HFC Male (Medium)",
        "file": "en_US-hfc_male-medium.onnx",
        "quality": "medium",
        "gender": "male"
    },
    {
        "id": "en_US-lessac-high",
        "name": "Lessac (High)",
        "file": "en_US-lessac-high.onnx",
        "quality": "high",
        "gender": "female"
    },
    {
        "id": "en_US-ryan-high",
        "name": "Ryan (High)",
        "file": "en_US-ryan-high.onnx",
        "quality": "high",
        "gender": "male"
    }
]

st.set_page_config(
    page_title="Piper Text-to-Speech",
    page_icon="🔊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .main-header {
        text-align: center;
        color: #1E88E5;
        margin-bottom: 2rem;
    }
    .stAudio {
        width: 100%;
    }
    .voice-name {
        font-weight: bold;
        color: #1E88E5;
    }
    .voice-quality {
        font-size: 0.8em;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🔊 Piper Text-to-Speech</h1>", unsafe_allow_html=True)

# Model paths
PIPER_DIR = Path("C:/piper")
MODELS_DIR = PIPER_DIR / "models"

# Get available models
def get_available_models():
    available_models = {}
    
    # Check models directory
    if MODELS_DIR.exists():
        for voice in VOICE_CONFIGS:
            model_path = MODELS_DIR / voice["file"]
            json_path = model_path.with_suffix('.onnx.json')
            if model_path.exists() and json_path.exists():
                available_models[voice["name"]] = {
                    "path": model_path,
                    "config": voice
                }
    
    return available_models

def generate_audio(text, model_info):
    try:
        # Create a temporary file for the output
        temp_dir = Path(tempfile.gettempdir())
        output_file = temp_dir / f"output_{int(time.time())}_{model_info['config']['id']}.wav"
        
        # Prepare piper command
        piper_cmd = [
            str(PIPER_DIR / "piper.exe"),
            "--model", str(model_info["path"]),
            "--output_file", str(output_file),
            "--json_config", str(model_info["path"].with_suffix('.onnx.json'))
        ]
        
        # Create process
        process = subprocess.Popen(
            piper_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PIPER_DIR)
        )
        
        # Send text directly to stdin
        stdout, stderr = process.communicate(input=text)
        
        if process.returncode == 0 and output_file.exists():
            return output_file.read_bytes()
        return None
    except Exception as e:
        return None

def split_into_sentences(text):
    # Split text into sentences using regex
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Remove empty sentences
    return [s for s in sentences if s.strip()]

def generate_mixed_voices_audio(text):
    sentences = split_into_sentences(text)
    if not sentences:
        return None
    
    # Get list of available models
    available_models = get_available_models()
    model_list = list(available_models.items())
    
    # Generate audio for each sentence with a different voice
    sentence_audios = []
    progress_bar = st.progress(0)
    
    for i, sentence in enumerate(sentences):
        # Pick a random voice for this sentence
        voice_name, voice_info = random.choice(model_list)
        
        # Generate audio for this sentence
        audio_bytes = generate_audio(sentence, voice_info)
        if audio_bytes:
            sentence_audios.append({
                "sentence": sentence,
                "audio": audio_bytes,
                "voice": voice_name,
                "config": voice_info["config"]
            })
        progress_bar.progress((i + 1) / len(sentences))
    
    return sentence_audios

# Verify piper installation
if not PIPER_DIR.exists():
    st.error(f"Piper directory not found at {PIPER_DIR}")
    st.stop()

if not (PIPER_DIR / "piper.exe").exists():
    st.error(f"Piper executable not found at {PIPER_DIR / 'piper.exe'}")
    st.stop()

# Sidebar for model selection
with st.sidebar:
    st.markdown("## Voice Settings")
    available_models = get_available_models()
    
    if not available_models:
        st.error("No models found in the models directory")
        st.stop()
    
    selected_model_name = st.selectbox(
        "Select Voice",
        options=list(available_models.keys()),
        help="Choose a voice model for text-to-speech conversion",
        index=list(available_models.keys()).index("HFC Female (Medium)" if "HFC Female (Medium)" in available_models else 0)
    )
    
    model_info = available_models[selected_model_name]
    
    # Show voice details
    st.markdown(f"""
    **Quality:** {model_info['config']['quality'].title()}  
    **Gender:** {model_info['config']['gender'].title()}
    """)
    
    st.markdown("---")
    
    # Generate in all voices button
    if st.button("🎭 Generate in All Voices", use_container_width=True):
        if 'current_text' in st.session_state and st.session_state.current_text:
            with st.spinner("Generating audio in all voices..."):
                all_audios = {}
                progress_bar = st.progress(0)
                for i, (name, info) in enumerate(available_models.items()):
                    audio_bytes = generate_audio(st.session_state.current_text, info)
                    if audio_bytes:
                        all_audios[name] = {
                            "audio": audio_bytes,
                            "config": info["config"]
                        }
                    progress_bar.progress((i + 1) / len(available_models))
                st.session_state.all_voices_audio = all_audios
                st.success(f"Generated audio in {len(all_audios)} voices!")
        else:
            st.warning("Please enter text first!")
    
    # Generate with mixed voices button
    if st.button("🎲 Mix Voices per Sentence", use_container_width=True):
        if 'current_text' in st.session_state and st.session_state.current_text:
            with st.spinner("Generating audio with mixed voices..."):
                sentence_audios = generate_mixed_voices_audio(st.session_state.current_text)
                if sentence_audios:
                    st.session_state.mixed_voices_audio = sentence_audios
                    st.success(f"Generated audio for {len(sentence_audios)} sentences!")
                else:
                    st.error("Failed to generate mixed voices audio.")
        else:
            st.warning("Please enter text first!")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app uses Piper TTS to convert text to speech.
    - Select a voice from the dropdown
    - Enter your text in the text area
    - Click 'Generate Audio' to convert
    - Click 'Generate in All Voices' to try all voices
    - Click 'Mix Voices per Sentence' for variety
    """)

# Main content
st.markdown("### Enter Text")
text_input = st.text_area(
    "Type or paste your text here:",
    height=200,
    help="Enter the text you want to convert to speech",
    key="text_input",
    on_change=lambda: setattr(st.session_state, 'current_text', st.session_state.text_input)
)

if st.button("🔊 Generate Audio", type="primary", use_container_width=True):
    if text_input:
        try:
            with st.spinner("Generating audio..."):
                audio_bytes = generate_audio(text_input, model_info)
                if audio_bytes:
                    st.session_state.last_audio = audio_bytes
                    st.session_state.last_text = text_input
                    st.session_state.last_model = model_info["config"]
                    st.success("Audio generated successfully!")
                else:
                    st.error("Failed to generate audio. Please try again or choose a different voice.")
        except Exception as e:
            st.error("An error occurred while generating audio. Please try again.")
    else:
        st.warning("Please enter some text first.")

# Single audio output section
if 'last_audio' in st.session_state:
    st.markdown("---")
    st.markdown("### Generated Audio")
    st.audio(st.session_state.last_audio, format="audio/wav")

# All voices output section
if 'all_voices_audio' in st.session_state and st.session_state.all_voices_audio:
    st.markdown("---")
    st.markdown("### All Voices")
    
    # Create a table for all voices
    for voice_name, voice_data in st.session_state.all_voices_audio.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"""
            <p class='voice-name'>{voice_name}</p>
            <p class='voice-quality'>{voice_data['config']['quality'].title()} Quality • {voice_data['config']['gender'].title()}</p>
            """, unsafe_allow_html=True)
        with col2:
            st.audio(voice_data["audio"], format="audio/wav")

# Mixed voices output section
if 'mixed_voices_audio' in st.session_state and st.session_state.mixed_voices_audio:
    st.markdown("---")
    st.markdown("### Mixed Voices")
    
    # Create a table for sentences with different voices
    for i, sentence_data in enumerate(st.session_state.mixed_voices_audio, 1):
        st.markdown(f"#### Sentence {i}")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown(f"""
            <p class='voice-name'>{sentence_data['voice']}</p>
            <p class='voice-quality'>{sentence_data['config']['quality'].title()} Quality • {sentence_data['config']['gender'].title()}</p>
            """, unsafe_allow_html=True)
        
        with col2:
            st.audio(sentence_data['audio'], format="audio/wav")
    
    # Join audio button
    if st.button("🔗 Join All Audio", type="primary", use_container_width=True):
        try:
            with st.spinner("Joining audio files..."):
                # Function to get wav params from bytes
                def get_wav_params(audio_bytes):
                    with wave.open(io.BytesIO(audio_bytes), 'rb') as wav:
                        return wav.getparams()
                
                # Get parameters from first audio file
                first_params = get_wav_params(st.session_state.mixed_voices_audio[0]['audio'])
                
                # Create output wave file
                output_bytes = io.BytesIO()
                with wave.open(output_bytes, 'wb') as output:
                    output.setparams(first_params)
                    
                    # Write each audio file's data
                    for sentence_data in st.session_state.mixed_voices_audio:
                        with wave.open(io.BytesIO(sentence_data['audio']), 'rb') as wav:
                            output.writeframes(wav.readframes(wav.getnframes()))
                
                # Store the joined audio in session state
                st.session_state.joined_audio = output_bytes.getvalue()
                st.success("Audio files joined successfully!")
        except Exception as e:
            st.error("Failed to join audio files. Please try again.")

# Joined audio output section
if 'joined_audio' in st.session_state:
    st.markdown("---")
    st.markdown("### Complete Audio")
    st.audio(st.session_state.joined_audio, format="audio/wav") 