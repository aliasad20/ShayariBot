# 🎙️ ShayariBot — Interview Preparation Guide

This guide breaks down your project from a high-level architectural view down to the specific technical implementations. Use this to confidently explain your project in any software engineering or AI/ML interview.

---

## 1. Project Overview (The "Elevator Pitch")
**"What did you build?"**
> "I built ShayariBot, a Mood-Based RAG (Retrieval-Augmented Generation) application that acts as an emotional companion. It uses an LLM to analyze a user's natural language input to detect their emotional state, queries a local ChromaDB vector database to retrieve the most resonant piece of classical poetry (Shayari), and then uses a generative AI voice cloning microservice to recite the poetry back to the user in a voice mathematically cloned from the original poet."

**Key Technologies:**
- **Frontend:** Streamlit
- **LLM/Routing:** Google Gemini (via `google-genai`), OpenAI fallback
- **Vector Database (RAG):** ChromaDB, Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Voice Synthesis:** Coqui XTTS_v2 (Few-Shot Voice Cloning)
- **Deployment:** Docker, Hugging Face Spaces

---

## 2. System Architecture & The "Dual-Environment" Solution

> [!IMPORTANT]
> **A major talking point for interviews:** Be sure to highlight the **Dual-Environment Architecture**. It shows strong systems engineering and problem-solving skills.

**The Problem:** Modern LLM libraries (Streamlit, Gemini API) require modern dependencies (e.g., Python 3.13, `numpy >= 2.0`). However, state-of-the-art open-source audio models (Coqui TTS, PyTorch CPU) rely on older, legacy dependencies (Python 3.10, `numpy < 2.0`). Attempting to install them together causes fatal dependency conflicts.
**The Solution:** You designed a **Microservice Architecture** using isolated virtual environments.
- The main app runs in `.venv` (Python 3.13).
- The voice cloning engine runs in `.venv_tts` (Python 3.10).
- The main app communicates with the TTS engine asynchronously by spawning a `subprocess` (the bridge), passing arguments via CLI, and retrieving the generated `.wav` file.

---

## 3. Step-by-Step Implementation Details

### A. Data Engineering (`data/shayaris.json` & `llm_dataset_updater.py`)
- **Implementation:** You curated a dataset of classical poetry (Allama Iqbal, Sahir Ludhianvi, Dinkar). 
- **Enhancement:** To ensure accurate voice synthesis, you wrote an LLM automation script (`llm_dataset_updater.py`) with **exponential backoff (retry logic)** to bypass API rate limits, parsing Urdu script into highly accurate Devanagari (`hindi_text`) so the TTS engine pronounces the words perfectly.

### B. Vector Ingestion (`backend/ingest.py`)
- **Implementation:** You used `sentence-transformers` to convert the text of the shayaris and their translations into dense vector embeddings. 
- **Usage:** These embeddings, alongside rich metadata (mood tags, emotional intensity, poet names), are persisted into a local SQLite-backed ChromaDB instance. 

### C. Mood Detection via LLM (`backend/mood_detector.py`)
- **Implementation:** Instead of simple keyword matching, you used a generative LLM (Gemini) acting as a classifier. You engineered a strict system prompt that forces the LLM to output a structured JSON response containing a `primary_mood`, `secondary_mood`, and `emotional_keywords`.
- **Usage:** This transforms messy, unstructured human emotion (e.g., "I feel so lost today") into structured, queryable data (e.g., `primary_mood: sadness`).

### D. The RAG Pipeline (`backend/rag_pipeline.py`)
- **Implementation:** This is the core retrieval engine. It takes the structured mood data and performs a **Hybrid Search**.
    1. **Semantic Search:** Queries ChromaDB using the emotional keywords.
    2. **Algorithmic Scoring:** You wrote a custom scoring algorithm that calculates a `Match Score`. It takes the base semantic distance and adds massive bonus multipliers if the database record's metadata (`mood_tags`) strictly matches the LLM's `primary_mood`.
- **Usage:** This ensures the AI doesn't just find a poem with similar *words*, but a poem with the exact *emotional resonance* the user needs.

### E. Few-Shot Voice Cloning (`backend/tts_engine.py` & `tts_worker.py`)
- **Implementation:** You implemented Coqui `XTTS_v2`, a state-of-the-art zero-shot voice cloning model. 
- **Few-Shot Upgrade:** Instead of a single audio sample, you wrote a globbing mechanism that finds *multiple* reference `.wav` files (e.g., `sahir_1.wav`, `sahir_sad.wav`) and feeds them all into the model simultaneously to average their acoustic profiles for a richer, more stable voice.
- **Dynamic Pacing:** You manipulated the engine's `speed` parameter dynamically based on the poet (e.g., slowing Dinkar down to `0.70` for dramatic gravitas).

---

## 4. Key Interview Questions to Anticipate

**Q: "Why did you use ChromaDB instead of a standard SQL database?"**
> A: "Because human emotions are nuanced. If a user types 'I feel like I'm drowning in an empty room', an SQL database requires exact keyword matches. ChromaDB uses semantic vector embeddings, allowing the system to understand the *meaning* of the phrase and match it to a poem about 'loneliness' even if those exact words aren't used."

**Q: "How did you handle the TTS engine reciting Urdu as Arabic?"**
> A: "Because Urdu uses the Arabic script block in Unicode, the TTS engine was misinterpreting the language and applying an Arabic accent. I solved this by explicitly disabling the Arabic fallback in `tts_engine.py` and creating a pipeline to ensure all records use either Roman transliteration (Hinglish) or Devanagari (Hindi) script, forcing the model into its highly accurate Hindi phonetic mode."

**Q: "How did you deploy this to the cloud?"**
> A: "I containerized the application using Docker. I wrote a custom `Dockerfile` based on Ubuntu that installs necessary Linux audio binaries (like `espeak-ng` and `libsndfile1`), uses the `deadsnakes` PPA to install multiple Python versions, and executes a shell script to build the dual virtual environments during the container build process. I then hosted this container seamlessly on Hugging Face Spaces."
