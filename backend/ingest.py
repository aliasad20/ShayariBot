"""
ingest.py — One-time script to embed shayaris into ChromaDB.
Run once: python backend/ingest.py
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "chroma_db"))
DATA_PATH = PROJECT_ROOT / "data" / "shayaris.json"
COLLECTION_NAME = "shayaris"


def get_embedding_text(shayari: dict) -> str:
    """Build a rich embedding string combining all semantic fields."""
    parts = [
        shayari.get("transliteration", ""),
        shayari.get("translation", ""),
        shayari.get("theme", ""),
        " ".join(shayari.get("mood_tags", [])),
        shayari.get("poet", ""),
        shayari.get("title", ""),
    ]
    return " | ".join(p for p in parts if p)


def setup_chromadb():
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

    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"🗑️ Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def ingest():
    print("🔷 Loading shayari dataset...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        shayaris = json.load(f)
    print(f"   Loaded {len(shayaris)} shayaris")

    print("🔷 Initializing ChromaDB...")
    collection = setup_chromadb()

    print("🔷 Embedding and storing shayaris...")
    batch_size = 10
    ids, documents, metadatas = [], [], []

    for shayari in shayaris:
        doc_text = get_embedding_text(shayari)
        metadata = {
            "poet": shayari.get("poet", "Unknown"),
            "poet_key": shayari.get("poet_key", shayari.get("id", "unknown").split("_")[0]),
            "title": shayari.get("title", ""),
            "collection": shayari.get("collection", ""),
            "language": shayari.get("language", "urdu"),
            "mood_tags": ",".join(shayari.get("mood_tags", [])),
            "theme": shayari.get("theme", ""),
            "emotional_intensity": float(shayari.get("emotional_intensity", 0.8) or 0.8),
            "shayari": shayari.get("shayari", ""),
            "transliteration": shayari.get("transliteration", ""),
            "translation": shayari.get("translation", ""),
            "hindi_text": shayari.get("hindi_text", ""),
        }
        ids.append(shayari["id"])
        documents.append(doc_text)
        metadatas.append(metadata)

        if len(ids) >= batch_size:
            collection.add(ids=ids, documents=documents, metadatas=metadatas)
            print(f"   ✓ Stored batch of {len(ids)}")
            ids, documents, metadatas = [], [], []

    # Store any remaining
    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"   ✓ Stored final batch of {len(ids)}")

    total = collection.count()
    print(f"\n✅ Ingestion complete! {total} shayaris stored in ChromaDB at: {CHROMA_PERSIST_DIR}")
    return total


if __name__ == "__main__":
    ingest()
