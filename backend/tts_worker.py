"""
tts_worker.py — Isolated Voice Cloning Microservice
This script is executed using the .venv_tts Python interpreter to prevent dependency conflicts.
"""

import sys
import os
import argparse

# Automatically accept Coqui TTS Terms of Service
os.environ["COQUI_TOS_AGREED"] = "1"

def synthesize(poet_key: str, tts_text: str, output_path: str, language: str):
    from TTS.api import TTS
    import torch
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[TTS Worker] Loading XTTS_v2 model on {device}... (This may take a minute)")
    
    # Load model
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    
    # Resolve absolute path to assets/voices
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    voices_dir = os.path.join(project_root, "assets", "voices")
    
    import glob
    ref_wav_paths = glob.glob(os.path.join(voices_dir, f"{poet_key}*.wav"))
    
    if not ref_wav_paths:
        print(f"[TTS Worker] ❌ Missing reference audio for: {poet_key}")
        sys.exit(1)
        
    print(f"[TTS Worker] Cloning voice for {poet_key} using {len(ref_wav_paths)} reference(s)...")
    
    speed_map = {
        "dinkar": 0.70,
        "sahir": 0.85,
        "iqbal": 0.85
    }
    speed = speed_map.get(poet_key, 0.85)
    
    tts.tts_to_file(
        text=tts_text,
        speaker_wav=ref_wav_paths,
        language=language,
        file_path=output_path,
        speed=speed
    )
    
    print("[TTS Worker] Generation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--poet_key", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--language", default="hi")
    
    args = parser.parse_args()
    
    synthesize(args.poet_key, args.text, args.output_path, args.language)
