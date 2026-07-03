import json
import os
import sys
import re
import uuid
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
DATA_FILE = "data/shayaris.json"
TARGET_COUNT = 500

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_json(text):
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())

def translate_batch_to_hindi(batch, client, model_name):
    prompt = f"""You are a linguistic expert in Urdu and Hindi. 
Below is a JSON array containing {len(batch)} shayaris. Many are in Urdu script.
Your task is to return the EXACT same JSON array, but add a new string field called "hindi_text" to each object.
The "hindi_text" must be the accurate, human-readable Devanagari (Hindi) script transliteration of the Urdu verse.
Use the existing "transliteration" field as a phonetic guide to ensure you write the correct Hindi words (e.g. including proper vowels and nuqtas).
If the "language" is already "hindi", just copy the "shayari" text into "hindi_text".

Input JSON:
{json.dumps(batch, ensure_ascii=False, indent=2)}

Return ONLY the updated JSON array, without any markdown formatting or extra text.
"""
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.1)
    )
    return extract_json(response.text)

def generate_new_shayaris(count, client, model_name):
    prompt = f"""You are an expert literary scholar. Generate {count} brand new, unique shayaris by famous poets (like Allama Iqbal, Sahir Ludhianvi, Ramdhari Singh Dinkar, Ghalib, Faiz).
    
Return the output EXACTLY as a JSON array of objects with this schema:
[
  {{
    "id": "will_be_generated",
    "poet": "Full Name",
    "poet_key": "lowercase_short_name",
    "title": "Title snippet",
    "shayari": "Native script text (Urdu or Hindi) with \\n",
    "transliteration": "Romanized phonetic text with \\n",
    "translation": "English translation with \\n",
    "hindi_text": "Highly accurate Devanagari (Hindi) script version of the verse (MANDATORY)",
    "collection": "Collection name",
    "language": "urdu" (or "hindi"),
    "mood_tags": ["sadness", "love", "loneliness", "patriotism", "rebellion", "spiritual", "hope", "heartbreak"],
    "theme": "brief theme",
    "emotional_intensity": 0.90
  }}
]
Do not include any other text outside the JSON array."""
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.7)
    )
    return extract_json(response.text)

def main():
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)
        
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    try:
        available_models = [m.name for m in client.models.list()]
        preferred_order = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        model_name = None
        for pref in preferred_order:
            if any(pref in m for m in available_models):
                model_name = next(m for m in available_models if pref in m)
                break
        if not model_name:
            model_name = available_models[0] if available_models else 'gemini-1.5-flash'
        
        # Strip the 'models/' prefix since generate_content does not expect it in this SDK version
        model_name = model_name.replace('models/', '')
    except Exception:
        model_name = "gemini-1.5-flash"
        
    print(f"Using model: {model_name}")
    data = load_data()
    
    # 1. Update existing shayaris
    missing_hindi = [item for item in data if "hindi_text" not in item]
    if missing_hindi:
        print(f"Found {len(missing_hindi)} shayaris missing 'hindi_text'. Translating via LLM in batches...")
        batch_size = 20
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            needs_update = [item for item in batch if "hindi_text" not in item]
            if not needs_update:
                continue
                
            print(f"Processing batch {i//batch_size + 1}...")
            try:
                updated_batch = translate_batch_to_hindi(batch, client, model_name)
                # Ensure the batch returned has the same length
                if len(updated_batch) == len(batch):
                    for j, item in enumerate(updated_batch):
                        data[i+j] = item
                    save_data(data)
                else:
                    print("Warning: LLM returned mismatched array length for batch. Skipping.")
                time.sleep(2) # rate limit pause
            except Exception as e:
                print(f"Error processing batch: {e}")
                break
        print("Finished updating existing shayaris.")
    else:
        print("All existing shayaris already have 'hindi_text'.")

    # 2. Generate new shayaris
    current_count = len(data)
    if current_count < TARGET_COUNT:
        print(f"\nCurrent count is {current_count}. Generating new shayaris to reach {TARGET_COUNT}...")
        while current_count < TARGET_COUNT:
            needed = min(15, TARGET_COUNT - current_count)
            print(f"Requesting {needed} new shayaris...")
            
            success = False
            retries = 0
            while not success and retries < 5:
                try:
                    new_items = generate_new_shayaris(needed, client, model_name)
                    for item in new_items:
                        item["id"] = f"{item.get('poet_key', 'unknown')}_{uuid.uuid4().hex[:8]}"
                    data.extend(new_items)
                    current_count = len(data)
                    save_data(data)
                    print(f"Added {len(new_items)} shayaris. Total: {current_count}")
                    success = True
                    time.sleep(2)
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str:
                        print(f"Rate limit hit (429). Waiting 60 seconds before retrying... (Attempt {retries+1}/5)")
                        time.sleep(60)
                        retries += 1
                    else:
                        print(f"Error generating new shayaris: {e}")
                        break
            
            if not success:
                print("Failed to generate new shayaris after multiple retries. Exiting generation loop.")
                break
    else:
        print(f"Dataset already has {current_count} shayaris. Target met.")
        
    print("\nRebuilding ChromaDB index...")
    os.system(f"{sys.executable} backend/ingest.py")
    print("Done! Restart Streamlit to see changes.")

if __name__ == "__main__":
    main()
