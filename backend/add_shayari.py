"""
add_shayari.py — Dynamically add or remove shayaris from ChromaDB + JSON.
No need to re-run ingest.py after adding new shayaris.
"""

import os
import json
import uuid
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "chroma_db"))
DATA_PATH = PROJECT_ROOT / "data" / "shayaris.json"
COLLECTION_NAME = "shayaris"

VALID_MOODS = ["sadness", "love", "loneliness", "patriotism", "rebellion", "spiritual", "hope", "heartbreak"]
VALID_POETS = ["iqbal", "sahir", "dinkar"]


_chroma_collection = None

def _get_collection():
    global _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection
        
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    # Disable telemetry to prevent Windows socket/multiprocessing errors
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
    _chroma_collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
    return _chroma_collection


def _build_embedding_text(shayari: dict) -> str:
    parts = [
        shayari.get("transliteration", ""),
        shayari.get("translation", ""),
        shayari.get("theme", ""),
        " ".join(shayari.get("mood_tags", [])),
        shayari.get("poet", ""),
        shayari.get("title", ""),
    ]
    return " | ".join(p for p in parts if p)


def add_shayari(
    poet_key: str,
    poet_display: str,
    title: str,
    shayari_text: str,
    transliteration: str,
    translation: str,
    hindi_text: str,
    collection_name: str,
    language: str,
    mood_tags: list[str],
    theme: str,
    emotional_intensity: float = 0.85,
) -> dict:
    """
    Add a new shayari to both ChromaDB and shayaris.json.
    Returns the created shayari dict with its generated ID.
    """
    # Validate
    if poet_key not in VALID_POETS:
        raise ValueError(f"Invalid poet_key '{poet_key}'. Must be one of: {VALID_POETS}")
    invalid_moods = [m for m in mood_tags if m not in VALID_MOODS]
    if invalid_moods:
        raise ValueError(f"Invalid mood(s): {invalid_moods}. Valid: {VALID_MOODS}")
    if not shayari_text.strip():
        raise ValueError("Shayari text cannot be empty.")

    # Build shayari dict
    shayari_id = f"{poet_key}_{uuid.uuid4().hex[:8]}"
    shayari = {
        "id": shayari_id,
        "poet": poet_display,
        "poet_key": poet_key,
        "title": title.strip(),
        "shayari": shayari_text.strip(),
        "transliteration": transliteration.strip(),
        "translation": translation.strip(),
        "hindi_text": hindi_text.strip(),
        "collection": collection_name.strip(),
        "language": language,
        "mood_tags": mood_tags,
        "theme": theme.strip(),
        "emotional_intensity": round(float(emotional_intensity), 2),
    }

    # 1. Add to ChromaDB
    chroma_collection = _get_collection()
    doc_text = _build_embedding_text(shayari)
    metadata = {
        "poet": shayari["poet"],
        "poet_key": shayari["poet_key"],
        "title": shayari["title"],
        "collection": shayari["collection"],
        "language": shayari["language"],
        "mood_tags": ",".join(shayari["mood_tags"]),
        "theme": shayari["theme"],
        "emotional_intensity": shayari["emotional_intensity"],
        "shayari": shayari["shayari"],
        "transliteration": shayari["transliteration"],
        "translation": shayari["translation"],
        "hindi_text": shayari["hindi_text"],
    }
    chroma_collection.add(
        ids=[shayari_id],
        documents=[doc_text],
        metadatas=[metadata],
    )

    # 2. Persist to shayaris.json
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        all_shayaris = json.load(f)
    all_shayaris.append(shayari)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_shayaris, f, ensure_ascii=False, indent=2)

    return shayari



def delete_shayari(shayari_id: str) -> bool:
    """
    Remove a shayari by ID from both ChromaDB and shayaris.json.
    Returns True if deleted, False if not found.
    """
    # 1. Remove from ChromaDB
    chroma_collection = _get_collection()
    existing = chroma_collection.get(ids=[shayari_id])
    if not existing["ids"]:
        return False
    chroma_collection.delete(ids=[shayari_id])

    # 2. Remove from shayaris.json
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        all_shayaris = json.load(f)
    original_count = len(all_shayaris)
    all_shayaris = [s for s in all_shayaris if s["id"] != shayari_id]
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_shayaris, f, ensure_ascii=False, indent=2)

    return len(all_shayaris) < original_count


def get_all_shayaris() -> list[dict]:
    """Return all shayaris from ChromaDB with their metadata."""
    chroma_collection = _get_collection()
    results = chroma_collection.get(include=["metadatas"])
    shayaris = []
    for i, sid in enumerate(results["ids"]):
        meta = results["metadatas"][i]
        shayaris.append({
            "id": sid,
            "poet": meta.get("poet", ""),
            "poet_key": meta.get("poet_key", ""),
            "title": meta.get("title", ""),
            "collection": meta.get("collection", ""),
            "language": meta.get("language", ""),
            "mood_tags": meta.get("mood_tags", "").split(","),
            "theme": meta.get("theme", ""),
            "emotional_intensity": meta.get("emotional_intensity", 0.8),
            "shayari": meta.get("shayari", ""),
            "transliteration": meta.get("transliteration", ""),
            "translation": meta.get("translation", ""),
            "hindi_text": meta.get("hindi_text", ""),
        })
    return sorted(shayaris, key=lambda x: x["poet_key"])


def get_db_stats() -> dict:
    """Return database statistics."""
    chroma_collection = _get_collection()
    results = chroma_collection.get(include=["metadatas"])
    total = len(results["ids"])
    by_poet = {}
    for meta in results["metadatas"]:
        poet = meta.get("poet_key", "unknown")
        by_poet[poet] = by_poet.get(poet, 0) + 1
    return {"total": total, "by_poet": by_poet}
