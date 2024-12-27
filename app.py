import streamlit as st
import tempfile
import os
import subprocess
from pathlib import Path
import time

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
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🔊 Piper Text-to-Speech</h1>", unsafe_allow_html=True)

# Model paths
PIPER_DIR = Path("C:/piper")
MODELS_DIR = PIPER_DIR / "models"

# Get available models
def get_available_models():
    models = []
    
    # Check models directory
    if MODELS_DIR.exists():
        for model in MODELS_DIR.glob("*.onnx"):
            # Get the corresponding JSON file
            json_file = model.with_suffix('.onnx.json')
            if json_file.exists():
                # Use the same name format as the working model
                new_name = f"en_US-{model.stem}"
                models.append((new_name, model))
    
    # Create a dictionary with clean names
    model_dict = {}
    for name, model in models:
        # Clean up name for display
        display_name = name.replace("-", " ").replace("_", " ")
        model_dict[display_name] = model
    
    return model_dict

def generate_audio(text, model_path):
    try:
        # Create a temporary file for the output
        temp_dir = Path(tempfile.gettempdir())
        output_file = temp_dir / f"output_{int(time.time())}_{model_path.stem}.wav"
        
        # Prepare piper command
        piper_cmd = [
            str(PIPER_DIR / "piper.exe"),
            "--model", str(model_path),
            "--output_file", str(output_file),
            "--json_config", str(model_path.with_suffix('.onnx.json'))
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
        help="Choose a voice model for text-to-speech conversion"
    )
    
    model_path = available_models[selected_model_name]
    
    st.markdown("---")
    
    # Generate in all voices button
    if st.button("🎭 Generate in All Voices", use_container_width=True):
        if 'current_text' in st.session_state and st.session_state.current_text:
            with st.spinner("Generating audio in all voices..."):
                all_audios = {}
                progress_bar = st.progress(0)
                for i, (name, model) in enumerate(available_models.items()):
                    audio_bytes = generate_audio(st.session_state.current_text, model)
                    if audio_bytes:
                        all_audios[name] = audio_bytes
                    progress_bar.progress((i + 1) / len(available_models))
                st.session_state.all_voices_audio = all_audios
                st.success(f"Generated audio in {len(all_audios)} voices!")
        else:
            st.warning("Please enter text first!")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app uses Piper TTS to convert text to speech.
    - Select a voice from the dropdown
    - Enter your text in the text area
    - Click 'Generate Audio' to convert
    - Or click 'Generate in All Voices' to try all voices
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
                audio_bytes = generate_audio(text_input, model_path)
                if audio_bytes:
                    st.session_state.last_audio = audio_bytes
                    st.session_state.last_text = text_input
                    st.session_state.last_model = selected_model_name
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
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.audio(st.session_state.last_audio, format="audio/wav")
    
    with col2:
        model_name = st.session_state.get('last_model', 'output').replace(" ", "_")
        st.download_button(
            label="📥 Download Audio",
            data=st.session_state.last_audio,
            file_name=f"piper_tts_{model_name}.wav",
            mime="audio/wav",
            use_container_width=True
        )
    
    with st.expander("Show Text Used"):
        st.text(st.session_state.last_text)

# All voices output section
if 'all_voices_audio' in st.session_state and st.session_state.all_voices_audio:
    st.markdown("---")
    st.markdown("### All Voices")
    
    # Create a table for all voices
    for voice_name, audio_data in st.session_state.all_voices_audio.items():
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            st.markdown(f"<p class='voice-name'>{voice_name}</p>", unsafe_allow_html=True)
        with col2:
            st.audio(audio_data, format="audio/wav")
        with col3:
            st.download_button(
                label="📥 Download",
                data=audio_data,
                file_name=f"piper_tts_{voice_name.replace(' ', '_')}.wav",
                mime="audio/wav",
                key=f"download_{voice_name}"
            ) 