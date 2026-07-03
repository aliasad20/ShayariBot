"""
tts_engine.py — Bridge to Isolated Voice Cloning Microservice
This runs in the main app environment and spawns the TTS worker in the .venv_tts environment.
"""

import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Per-Poet Voice Configuration
# ─────────────────────────────────────────────
POET_VOICE_CONFIG = {
    "iqbal": {
        "name": "Allama Iqbal",
        "description": "Deep baritone — spiritual, philosophical gravitas (Requires iqbal.wav)",
        "voice_name": "Allama Iqbal"
    },
    "sahir": {
        "name": "Sahir Ludhianvi",
        "description": "Lyrical, melancholic — conversational (Requires sahir.wav)",
        "voice_name": "Sahir Ludhianvi"
    },
    "dinkar": {
        "name": "Ramdhari Singh Dinkar",
        "description": "Powerful, nationalistic — dramatic (Requires dinkar.wav)",
        "voice_name": "Ramdhari Singh Dinkar"
    }
}

def get_tts_text(shayari: dict) -> str:
    """
    Build the best text string for TTS.
    Always prefer native script for better pronunciation.
    """
    # We now expect every shayari to have a 'hindi_text' field pre-computed in the dataset.
    # This guarantees the TTS model reads in Devanagari script for accurate pronunciation.
    raw = shayari.get("hindi_text", "")
    if not raw:
        # If hindi_text is missing from the DB, fallback to transliteration (Hinglish)
        # We explicitly DO NOT fallback to the raw Urdu shayari to prevent Arabic recitation.
        raw = shayari.get("transliteration", "")

    lines = [line.strip() for line in raw.strip().split("\n") if line.strip()]
    return " ... ".join(lines)


import re

def detect_text_language(text: str) -> str:
    """
    Since we only want Hindi speech, we strictly use 'hi'. 
    If the text is Romanized (transliteration), XTTS 'en' can read it, but 'hi' often works better for Hinglish.
    """
    if re.search(r'[a-zA-Z]', text) and not re.search(r'[\u0900-\u097F]', text):
        return "en" # Use English phonetics for roman transliteration
    return "hi"  # Default to Hindi

def synthesize_speech(shayari: dict) -> bytes | None:
    """
    Spawns the isolated TTS microservice to generate speech.
    Returns raw WAV bytes or None if TTS fails.
    """
    poet_key = shayari.get("poet_key", "iqbal")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if .venv_tts exists
    venv_tts_path = os.path.join(project_root, ".venv_tts")
    python_exe = os.path.join(venv_tts_path, "bin", "python") if os.name != 'nt' else os.path.join(venv_tts_path, "Scripts", "python.exe")
    
    if not os.path.exists(python_exe):
        print(f"[TTS] ❌ TTS Environment missing. Please run setup.bat again.")
        return None
        
    import glob
    voices_dir = os.path.join(project_root, "assets", "voices")
    ref_wavs = glob.glob(os.path.join(voices_dir, f"{poet_key}*.wav"))
    
    if not ref_wavs:
        print(f"[TTS] ❌ Missing reference audio for: {poet_key}")
        fallback_wavs = glob.glob(os.path.join(voices_dir, "sahir*.wav"))
        if fallback_wavs:
            print(f"[TTS] ⚠️ Falling back to sahir's voice profile")
            poet_key = "sahir"
        else:
            print("[TTS] Please provide at least one .wav file in assets/voices to clone.")
            return None

    tts_text = get_tts_text(shayari)
    
    # Determine the correct XTTS language code by inspecting the text characters
    xtts_lang = detect_text_language(tts_text)
    
    output_path = os.path.join(project_root, "assets", "voices", "temp_output.wav")
    worker_script = os.path.join(project_root, "backend", "tts_worker.py")

    try:
        print(f"[TTS] Bridging to isolated Voice Cloning environment for {poet_key}...")
        
        # Ensure the worker uses UTF-8 to prevent UnicodeEncodeError on Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # Execute the worker in the isolated environment
        result = subprocess.run([
            python_exe, worker_script,
            "--poet_key", poet_key,
            "--text", tts_text,
            "--output_path", output_path,
            "--language", xtts_lang
        ], capture_output=True, text=True, encoding="utf-8", env=env)
        
        if result.returncode != 0:
            print(f"[TTS] Worker failed with return code {result.returncode}. Error details:")
            print(result.stderr or "No stderr output captured.")
            with open(os.path.join(project_root, "tts_error.log"), "w", encoding="utf-8") as f:
                f.write(result.stderr or "No stderr output captured.")
            return None
            
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                audio_bytes = f.read()
            
            # Clean up temp file
            os.remove(output_path)
            return audio_bytes
                
    except Exception as e:
        print(f"[TTS] Bridge failed: {e}")
        return None

def get_voice_info(poet_key: str) -> dict:
    """Return voice metadata for display in UI."""
    return POET_VOICE_CONFIG.get(poet_key, POET_VOICE_CONFIG["iqbal"])
