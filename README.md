---
title: ShayariBot
emoji: 🎭
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# 🎙️ ShayariBot — Poetry for Your Soul

A mood-based RAG (Retrieval-Augmented Generation) application that reads your emotional state and finds the perfect shayari from **Allama Iqbal**, **Sahir Ludhianvi**, or **Ramdhari Singh Dinkar** — then recites it in a voice closest to the poet.

---

## ✨ Features

- 🧠 **AI Mood Detection** — Understands your emotional state from natural language (Google Gemini / OpenAI)
- 🔍 **RAG Retrieval** — Hybrid semantic + mood-tag search via ChromaDB returns the single best-matching shayari
- 🎙️ **Per-Poet Voice** — ElevenLabs TTS with distinct voice profiles for each poet
- 🌙 **Premium Dark UI** — Gold-accented Streamlit interface with RTL Urdu + Hindi support
- 📖 **8 Mood Categories** — sadness, love, loneliness, patriotism, rebellion, spiritual, hope, heartbreak

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd RAG_Project
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your keys:
# - GOOGLE_API_KEY (free at https://aistudio.google.com)
# - ELEVENLABS_API_KEY (free tier at https://elevenlabs.io)
```

### 3. Ingest Shayaris into ChromaDB

```bash
python backend/ingest.py
```

This runs **once** and builds the local vector database. You'll see:
```
✅ Ingestion complete! 40 shayaris stored in ChromaDB
```

### 4. Run the App

```bash
streamlit run app/main.py
```

Open http://localhost:8501 in your browser.

---

## 🗂️ Project Structure

```
RAG_Project/
├── app/
│   └── main.py              # Streamlit UI
├── backend/
│   ├── mood_detector.py     # LLM mood classification
│   ├── rag_pipeline.py      # ChromaDB retrieval + LLM context
│   ├── tts_engine.py        # ElevenLabs per-poet voice
│   └── ingest.py            # One-time ChromaDB ingestion
├── data/
│   └── shayaris.json        # Curated shayari dataset
├── chroma_db/               # Auto-created vector store
├── .streamlit/
│   └── config.toml          # Dark theme config
├── .env.example             # API keys template
├── requirements.txt
└── README.md
```

---

## 🌐 Deployment

### Streamlit Community Cloud (Free, Recommended)

1. Push your code to GitHub (do **not** commit your `.env` file)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New App
3. Set **Main file path**: `app/main.py`
4. Add your secrets in the **Secrets** tab (TOML format):
   ```toml
   GOOGLE_API_KEY = "your_key"
   ELEVENLABS_API_KEY = "your_key"
   LLM_PROVIDER = "gemini"
   ```
5. **Important**: Add a `packages.txt` file for system dependencies if needed, and pre-ingest your ChromaDB by committing the `chroma_db/` folder to your repo.

### Render (Alternative)

```yaml
# render.yaml
services:
  - type: web
    name: shayaribot
    env: python
    buildCommand: pip install -r requirements.txt && python backend/ingest.py
    startCommand: streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
      - key: ELEVENLABS_API_KEY
        sync: false
```

---

## 🔑 API Keys Guide

| Key | Where to Get | Cost |
|-----|-------------|------|
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Free (Gemini Flash) |
| `ELEVENLABS_API_KEY` | [elevenlabs.io](https://elevenlabs.io) | Free (10K chars/month) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | Optional, paid |

---

## 🎭 The Poets

| Poet | Language | Voice Style | Speciality |
|------|----------|-------------|-----------|
| 🦅 **Allama Iqbal** | Urdu/Persian | Deep baritone, spiritual | Selfhood, faith, existentialism |
| 🌙 **Sahir Ludhianvi** | Urdu/Hindi | Lyrical, melancholic | Love, heartbreak, social justice |
| 🔥 **Ramdhari Singh Dinkar** | Hindi | Powerful, commanding | Patriotism, valor, righteousness |

---

## 🛠️ Customization

### Add More Shayaris
Edit `data/shayaris.json` and re-run `python backend/ingest.py`.

### Change Voice IDs
Edit `backend/tts_engine.py` → `POET_VOICE_CONFIG` and replace `voice_id` with any [ElevenLabs voice](https://elevenlabs.io/voice-library).

### Switch LLM
In `.env`, set `LLM_PROVIDER=openai` and add your `OPENAI_API_KEY`.

---

*"شعر وہ ہے جو دل میں اتر جائے" — Poetry is what sinks into the heart.*
