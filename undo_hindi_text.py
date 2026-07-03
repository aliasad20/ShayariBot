import json
import os

DATA_FILE = "data/shayaris.json"

def undo_changes():
    if not os.path.exists(DATA_FILE):
        print(f"Error: Could not find {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for item in data:
        if "hindi_text" in item:
            del item["hindi_text"]
            updated += 1

    if updated > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully removed hindi_text from {updated} shayaris!")
    else:
        print("No hindi_text fields found to remove.")

if __name__ == "__main__":
    undo_changes()
