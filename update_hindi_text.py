import json
import os
import sys

# Ensure you have aksharamukha installed: pip install aksharamukha
try:
    from aksharamukha import transliterate
except ImportError:
    print("Please install the required package by running: pip install aksharamukha")
    sys.exit(1)

DATA_FILE = "data/shayaris.json"

def process_existing():
    if not os.path.exists(DATA_FILE):
        print(f"Error: Could not find {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Processing existing shayaris to add 'hindi_text'...")
    updated = 0
    
    for item in data:
        lang = item.get("language", "urdu").lower()
        raw = item.get("shayari", "")
        
        # Check if hindi_text is missing or if we want to overwrite it
        if "hindi_text" not in item:
            if lang == "urdu":
                # Transliterate Urdu script to Devanagari (Hindi)
                item["hindi_text"] = transliterate.process('Urdu', 'Devanagari', raw)
            else:
                # If it's already hindi, just copy it
                item["hindi_text"] = raw
            updated += 1

    if updated > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully added hindi_text to {updated} shayaris!")
        
        # Re-build ChromaDB index to reflect dataset changes
        print("\nRebuilding ChromaDB index...")
        os.system(f"{sys.executable} backend/ingest.py")
    else:
        print("All existing shayaris already have hindi_text. No changes needed.")

if __name__ == "__main__":
    process_existing()
    print("Done! You can now restart Streamlit.")
