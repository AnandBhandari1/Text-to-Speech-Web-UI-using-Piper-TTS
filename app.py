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
import numpy as np
from scipy.io import wavfile

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
    /* Dark theme colors */
    :root {
        --bg-color: #0E1117;
        --card-bg: #1E1E1E;
        --text-color: #C6C6C6;
        --accent-color: #31333F;
        --border-color: #2D3139;
        --header-color: #C6C6C6;
        --subtext-color: #808080;
        --button-color: #262730;
        --button-hover: #31333F;
    }

    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }

    .main-header {
        text-align: center;
        color: var(--header-color);
        margin-bottom: 2rem;
    }

    .stAudio {
        width: 100%;
        margin: 0.5rem 0;
    }

    .voice-name {
        font-weight: 500;
        color: var(--text-color);
        margin: 0;
        font-size: 1em;
    }

    .voice-quality {
        font-size: 0.85em;
        color: var(--subtext-color);
        margin: 0;
        padding-top: 0.2rem;
    }

    .sentence-text {
        color: var(--text-color);
        font-size: 0.9em;
        margin: 0.5rem 0;
        padding: 0.5rem;
        background: var(--accent-color);
        border-radius: 4px;
    }

    .section-header {
        color: var(--header-color);
        padding: 0.5rem 0;
        margin: 0.5rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    .voice-card {
        background: var(--card-bg);
        padding: 0.8rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        border: 1px solid var(--border-color);
    }

    .stButton button {
        background-color: var(--button-color) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-color) !important;
    }

    .stButton button:hover {
        background-color: var(--button-hover) !important;
        border: 1px solid var(--border-color) !important;
    }

    .text-area-label {
        color: var(--header-color);
    }

    .stTextArea textarea {
        background-color: var(--card-bg);
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }

    .voice-info {
        background: var(--card-bg);
        padding: 0.8rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        border: 1px solid var(--border-color);
        color: var(--text-color);
    }

    /* Override Streamlit's default styles */
    .stMarkdown {
        color: var(--text-color);
    }

    .stSelectbox label {
        color: var(--text-color) !important;
    }

    .stSelectbox div[data-baseweb="select"] {
        background-color: var(--card-bg) !important;
        border-color: var(--border-color) !important;
    }

    .stSelectbox div[data-baseweb="select"] * {
        color: var(--text-color) !important;
    }

    .stProgress > div > div {
        background-color: var(--accent-color) !important;
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
    
    # Get list of available models in the same order as VOICE_CONFIGS
    available_models = get_available_models()
    ordered_models = []
    for voice in VOICE_CONFIGS:
        if voice["name"] in available_models:
            ordered_models.append((voice["name"], available_models[voice["name"]]))
    
    if not ordered_models:
        return None
    
    # Generate audio for each sentence with voices in sequence
    sentence_audios = []
    progress_bar = st.progress(0)
    
    for i, sentence in enumerate(sentences):
        # Use voice in sequence, loop back to start if needed
        voice_index = i % len(ordered_models)
        voice_name, voice_info = ordered_models[voice_index]
        
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

def create_silence(duration_seconds, sample_rate, num_channels):
    # Create silence as a numpy array
    num_samples = int(duration_seconds * sample_rate)
    return np.zeros(num_samples * num_channels, dtype=np.int16)

def generate_single_voice_with_gaps(text, model_info):
    try:
        sentences = split_into_sentences(text)
        if not sentences:
            return None
            
        # Generate audio for each sentence
        audio_segments = []
        progress_bar = st.progress(0)
        
        for i, sentence in enumerate(sentences):
            audio_bytes = generate_audio(sentence, model_info)
            if audio_bytes:
                with io.BytesIO(audio_bytes) as bio:
                    with wave.open(bio, 'rb') as wav:
                        if not audio_segments:  # First segment
                            target_sample_rate = wav.getframerate()
                            target_channels = wav.getnchannels()
                            target_sampwidth = wav.getsampwidth()
                        frames = wav.readframes(wav.getnframes())
                        audio_segments.append({
                            'frames': frames,
                            'sample_rate': wav.getframerate(),
                            'channels': wav.getnchannels(),
                            'sampwidth': wav.getsampwidth()
                        })
            progress_bar.progress((i + 1) / len(sentences))
        
        if not audio_segments:
            return None
            
        # Create output wave file with gaps
        output_bytes = io.BytesIO()
        with wave.open(output_bytes, 'wb') as output:
            output.setnchannels(target_channels)
            output.setsampwidth(target_sampwidth)
            output.setframerate(target_sample_rate)
            
            # Create 1-second silence
            silence = create_silence(1.0, target_sample_rate, target_channels)
            
            # Write each audio segment with silence in between
            for i, segment in enumerate(audio_segments):
                # Convert frames to numpy array
                audio_data = np.frombuffer(segment['frames'], dtype=np.int16)
                
                # If sample rates don't match, we need to resample
                if segment['sample_rate'] != target_sample_rate:
                    ratio = target_sample_rate / segment['sample_rate']
                    new_length = int(len(audio_data) * ratio)
                    indices = np.linspace(0, len(audio_data) - 1, new_length)
                    audio_data = np.interp(indices, np.arange(len(audio_data)), audio_data)
                
                # Write the audio segment
                output.writeframes(audio_data.astype(np.int16).tobytes())
                
                # Add silence after each segment except the last one
                if i < len(audio_segments) - 1:
                    output.writeframes(silence.tobytes())
        
        return output_bytes.getvalue()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Verify piper installation
if not PIPER_DIR.exists():
    st.error(f"Piper directory not found at {PIPER_DIR}")
    st.stop()

if not (PIPER_DIR / "piper.exe").exists():
    st.error(f"Piper executable not found at {PIPER_DIR / 'piper.exe'}")
    st.stop()

# Sidebar for model selection
with st.sidebar:
    st.markdown("## 🎤 Voice Settings")
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
    <div class='voice-info'>
    ✨ **Quality:** {model_info['config']['quality'].title()}<br>
    👤 **Gender:** {model_info['config']['gender'].title()}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Actions")
    
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
    
    # Generate with single voice and gaps button
    if st.button("🎵 Generate with Gaps", use_container_width=True):
        if 'current_text' in st.session_state and st.session_state.current_text:
            with st.spinner("Generating audio with gaps..."):
                joined_audio = generate_single_voice_with_gaps(st.session_state.current_text, model_info)
                if joined_audio:
                    st.session_state.joined_audio = joined_audio
                    st.success("Audio generated successfully!")
                else:
                    st.error("Failed to generate audio.")
        else:
            st.warning("Please enter text first!")
    
    st.markdown("---")
    st.markdown("""
    <div class='about-section'>
    <h3>ℹ️ About</h3>
    <p>This app uses Piper TTS to convert text to speech.</p>
    <ul>
    <li>Select a voice from the dropdown</li>
    <li>Enter your text in the text area</li>
    <li>Click 'Generate Audio' to convert</li>
    <li>Click 'Generate in All Voices' to try all voices</li>
    <li>Click 'Mix Voices per Sentence' for variety</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Main content
st.markdown("<h3 class='section-header'>✍️ Enter Text</h3>", unsafe_allow_html=True)
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
    st.markdown("<h3 class='section-header'>🎵 Generated Audio</h3>", unsafe_allow_html=True)
    st.audio(st.session_state.last_audio, format="audio/wav")

# All voices output section
if 'all_voices_audio' in st.session_state and st.session_state.all_voices_audio:
    st.markdown("<h3 class='section-header'>🎭 All Voices</h3>", unsafe_allow_html=True)
    
    # Create a table for all voices
    for voice_name, voice_data in st.session_state.all_voices_audio.items():
        st.markdown("<div class='voice-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"""
            <p class='voice-name'>{voice_name}</p>
            <p class='voice-quality'>✨ {voice_data['config']['quality'].title()} Quality<br>
            👤 {voice_data['config']['gender'].title()}</p>
            """, unsafe_allow_html=True)
        with col2:
            st.audio(voice_data["audio"], format="audio/wav")
        st.markdown("</div>", unsafe_allow_html=True)

# Mixed voices output section
if 'mixed_voices_audio' in st.session_state and st.session_state.mixed_voices_audio:
    st.markdown("<h3 class='section-header'>🎲 Mixed Voices</h3>", unsafe_allow_html=True)
    
    for sentence_data in st.session_state.mixed_voices_audio:
        # st.markdown("<div class='voice-card'>", unsafe_allow_html=True)
        # Display sentence text
        st.markdown(f"<div class='sentence-text'>{sentence_data['sentence']}</div>", unsafe_allow_html=True)
        # Display voice name and audio
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"""
            <p class='voice-name'>{sentence_data['voice']}</p>
            <p class='voice-quality'>{sentence_data['config']['quality'].title()} • {sentence_data['config']['gender'].title()}</p>
            """, unsafe_allow_html=True)
        with col2:
            st.audio(sentence_data['audio'], format="audio/wav")
        # st.markdown("</div>", unsafe_allow_html=True)
    
    # Join audio button
    if st.button("🔗 Join All Audio", type="primary", use_container_width=True):
        try:
            with st.spinner("Joining audio files..."):
                # Read all audio files and their parameters
                audio_segments = []
                target_sample_rate = None
                
                # First pass: read all files and determine target sample rate
                for sentence_data in st.session_state.mixed_voices_audio:
                    with io.BytesIO(sentence_data['audio']) as bio:
                        with wave.open(bio, 'rb') as wav:
                            if target_sample_rate is None:
                                target_sample_rate = wav.getframerate()
                                target_channels = wav.getnchannels()
                                target_sampwidth = wav.getsampwidth()
                            
                            # Read the frames
                            frames = wav.readframes(wav.getnframes())
                            audio_segments.append({
                                'frames': frames,
                                'sample_rate': wav.getframerate(),
                                'channels': wav.getnchannels(),
                                'sampwidth': wav.getsampwidth()
                            })
                
                # Create output wave file
                output_bytes = io.BytesIO()
                with wave.open(output_bytes, 'wb') as output:
                    output.setnchannels(target_channels)
                    output.setsampwidth(target_sampwidth)
                    output.setframerate(target_sample_rate)
                    
                    # Create 2-second silence
                    silence = create_silence(1.0, target_sample_rate, target_channels)
                    
                    # Write each audio segment with silence in between
                    for i, segment in enumerate(audio_segments):
                        # Convert frames to numpy array
                        audio_data = np.frombuffer(segment['frames'], dtype=np.int16)
                        
                        # If sample rates don't match, we need to resample
                        if segment['sample_rate'] != target_sample_rate:
                            # Calculate resampling ratio
                            ratio = target_sample_rate / segment['sample_rate']
                            new_length = int(len(audio_data) * ratio)
                            # Resample using numpy
                            indices = np.linspace(0, len(audio_data) - 1, new_length)
                            audio_data = np.interp(indices, np.arange(len(audio_data)), audio_data)
                        
                        # Write the audio segment
                        output.writeframes(audio_data.astype(np.int16).tobytes())
                        
                        # Add silence after each segment except the last one
                        if i < len(audio_segments) - 1:
                            output.writeframes(silence.tobytes())
                
                # Store the joined audio in session state
                st.session_state.joined_audio = output_bytes.getvalue()
                st.success("Audio files joined successfully!")
        except Exception as e:
            st.error(f"Failed to join audio files: {str(e)}")

# Joined audio output section
if 'joined_audio' in st.session_state:
    st.markdown("<h3 class='section-header'>🎵 Complete Audio</h3>", unsafe_allow_html=True)
    # st.markdown("<div class='voice-card'>", unsafe_allow_html=True)
    st.audio(st.session_state.joined_audio, format="audio/wav")
    # st.markdown("</div>", unsafe_allow_html=True) 