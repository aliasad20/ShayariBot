"""
rag_pipeline.py — Core RAG retrieval + LLM context generation.
Retrieves the single BEST matching shayari for a given mood/message.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "chroma_db"))
COLLECTION_NAME = "shayaris"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

CONTEXT_SYSTEM_PROMPT = """You are a profound literary scholar deeply versed in Urdu and Hindi poetry — specifically the works of Allama Iqbal, Sahir Ludhianvi, and Ramdhari Singh Dinkar.

A user has shared their emotional state. You have found the perfect shayari for them.

Your task is to write a beautiful, empathetic 2-3 sentence explanation of:
1. Why this specific shayari speaks to their current emotional state
2. The deeper meaning or feeling the poet captured
3. How it might bring comfort, perspective, or resonance to the user

Write in a warm, intimate tone — like a knowledgeable friend sharing poetry at a candlelit gathering.
Write ONLY the explanation, no titles or headers.
CRITICAL RULE: DO NOT rewrite, translate, or output the shayari verses yourself in your response. The poetry is already visible to the user. ONLY output the psychological/emotional explanation."""


_chroma_collection = None

def get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection
        
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    # Disable telemetry and set singleton to prevent Windows socket/multiprocessing errors
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Optional: set env var to silence HuggingFace warnings
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
    _chroma_collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
    return _chroma_collection


def build_query(user_message: str, mood_data: dict) -> str:
    """Build a rich semantic query from user message + mood analysis."""
    mood = mood_data.get("primary_mood", "")
    secondary = mood_data.get("secondary_mood", "")
    keywords = " ".join(mood_data.get("emotional_keywords", []))
    theme = mood_data.get("mood_description", "")
    return f"{user_message} | {mood} {secondary} | {keywords} | {theme}"


def retrieve_best_shayari(user_message: str, mood_data: dict) -> dict | None:
    """Retrieve the single best-matching shayari from ChromaDB."""
    try:
        collection = get_chroma_collection()
        query = build_query(user_message, mood_data)

        # Primary: semantic search weighted by mood
        results = collection.query(
            query_texts=[query],
            n_results=30, # Fetch more to allow strict filtering
            include=["documents", "metadatas", "distances"]
        )

        if not results["ids"][0]:
            return None

        candidates = []
        strict_candidates = []
        mood_tags_primary = mood_data.get("primary_mood", "")
        mood_tags_secondary = mood_data.get("secondary_mood", "")

        for i, meta in enumerate(results["metadatas"][0]):
            shayari_moods = meta.get("mood_tags", "").split(",")
            distance = results["distances"][0][i]

            # Compute a combined score: semantic similarity + mood match bonus
            mood_score = 0
            has_primary = mood_tags_primary in shayari_moods
            if has_primary:
                mood_score += 0.50  # Massive boost for primary mood match
            if mood_tags_secondary in shayari_moods:
                mood_score += 0.15

            # ChromaDB cosine distance → similarity (lower = more similar)
            semantic_score = 1 - distance

            # Emotional intensity bonus (prefer evocative shayaris)
            intensity_bonus = float(meta.get("emotional_intensity", 0.8)) * 0.1

            combined_score = semantic_score + mood_score + intensity_bonus
            item = (combined_score, meta, results["ids"][0][i])
            candidates.append(item)
            
            if has_primary:
                strict_candidates.append(item)

        # If we found strict matches for the primary mood, ONLY pick from those!
        if strict_candidates:
            candidates = strict_candidates

        # Pick randomly from the top 5 best matching shayaris for maximum variety but high relevance
        candidates.sort(key=lambda x: x[0], reverse=True)
        import random
        # Take up to top 5
        top_candidates = candidates[:5]
        best_score, best_meta, best_id = random.choice(top_candidates)

        return {
            "id": best_id,
            "poet": best_meta["poet"],
            "poet_key": best_meta["poet_key"],
            "title": best_meta["title"],
            "collection": best_meta["collection"],
            "language": best_meta["language"],
            "shayari": best_meta["shayari"],
            "transliteration": best_meta["transliteration"],
            "translation": best_meta["translation"],
            "hindi_text": best_meta.get("hindi_text", ""),
            "mood_tags": best_meta["mood_tags"].split(","),
            "theme": best_meta["theme"],
            "emotional_intensity": best_meta["emotional_intensity"],
            "match_score": round(best_score, 3)
        }

    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        return None


def generate_context_gemini(user_message: str, shayari: dict, mood_data: dict) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    available_models = [m.name for m in client.models.list()]
    
    preferred_order = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.0-pro', 'gemini-1.5-pro']
    model_name = None
    for pref in preferred_order:
        if any(pref in m for m in available_models):
            model_name = next(m for m in available_models if pref in m)
            break

    if not model_name:
        model_name = available_models[0] if available_models else 'gemini-1.5-flash'
        
    model_name = model_name.replace('models/', '')
    
    prompt = f"""User's message: "{user_message}"
User's mood: {mood_data.get('primary_mood', 'unknown')} ({mood_data.get('mood_description', '')})

Poet: {shayari['poet']}
Shayari: {shayari['transliteration']}
Translation: {shayari['translation']}
Theme: {shayari['theme']}"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=CONTEXT_SYSTEM_PROMPT,
        )
    )
    return response.text.strip()


def generate_context_openai(user_message: str, shayari: dict, mood_data: dict) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""User's message: "{user_message}"
User's mood: {mood_data.get('primary_mood', 'unknown')} ({mood_data.get('mood_description', '')})

Poet: {shayari['poet']}
Shayari: {shayari['transliteration']}
Translation: {shayari['translation']}
Theme: {shayari['theme']}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CONTEXT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


def generate_context_fallback(shayari: dict, mood_data: dict) -> str:
    mood = mood_data.get("primary_mood", "this feeling")
    poet = shayari["poet"]
    theme = shayari.get("theme", "the human experience")
    return (
        f"{poet} understood {mood} deeply, as reflected in this verse about {theme}. "
        f"This shayari carries the weight of emotions that words alone often fail to express. "
        f"Let these lines be a companion to your heart right now."
    )


def generate_context(user_message: str, shayari: dict, mood_data: dict) -> str:
    """Generate a contextual explanation using the configured LLM."""
    try:
        if LLM_PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
            return generate_context_openai(user_message, shayari, mood_data)
        elif os.getenv("GOOGLE_API_KEY"):
            return generate_context_gemini(user_message, shayari, mood_data)
        else:
            return generate_context_fallback(shayari, mood_data)
    except Exception as e:
        print(f"[RAG] Context generation failed: {e}")
        return generate_context_fallback(shayari, mood_data)


def get_shayari(user_message: str, mood_data: dict) -> dict | None:
    """
    Full RAG pipeline: retrieve best shayari + generate contextual explanation.
    Returns a complete response dict or None on failure.
    """
    # 1. Retrieve best shayari
    shayari = retrieve_best_shayari(user_message, mood_data)
    if not shayari:
        return None

    # 2. Generate LLM context
    context = generate_context(user_message, shayari, mood_data)

    return {
        **shayari,
        "why_this_shayari": context,
        "mood_data": mood_data
    }


if __name__ == "__main__":
    from backend.mood_detector import detect_mood

    test_inputs = [
        "I feel completely heartbroken and empty inside",
        "I am proud of my country and want to serve it",
        "I am searching for peace and divine connection",
        "I am angry at the injustice in society",
        "I miss my love so deeply it hurts"
    ]

    for msg in test_inputs:
        print(f"\n{'='*60}")
        print(f"Input: {msg}")
        mood = detect_mood(msg)
        print(f"Mood: {mood['primary_mood']}")
        result = get_shayari(msg, mood)
        if result:
            print(f"Poet: {result['poet']}")
            print(f"Title: {result['title']}")
            print(f"Shayari:\n{result['transliteration']}")
            print(f"Context: {result['why_this_shayari']}")
        else:
            print("No result found.")
