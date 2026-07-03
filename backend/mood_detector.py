import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

MOOD_SYSTEM_PROMPT = """You are an expert literary emotional analyst. Given a user's message expressing their feelings or current state of mind, you must:

1. Detect the PRIMARY mood from this exact list: sadness, love, loneliness, patriotism, rebellion, spiritual, hope, heartbreak
2. Detect a SECONDARY mood (can be same or different) from the same list
3. Extract 3-5 emotional keywords from the user's message
4. Suggest which poet(s) from [iqbal, sahir, dinkar] would resonate most

Respond in this exact JSON format only (no markdown, no extra text):
{
  "primary_mood": "<mood>",
  "secondary_mood": "<mood>",
  "emotional_keywords": ["word1", "word2", "word3"],
  "suggested_poets": ["poet1", "poet2"],
  "mood_description": "<one sentence describing the emotional state>"
}

MOOD GUIDE:
- sadness: grief, loss, pain, crying, melancholy
- love: affection, romance, longing, devotion, missing someone
- loneliness: isolation, alone, abandoned, empty, disconnected
- patriotism: nation, homeland, pride, sacrifice, freedom
- rebellion: anger at injustice, defiance, protest, fighting the system
- spiritual: faith, God, divine, prayer, seeking meaning
- hope: optimism, future, dreams, recovery, new beginnings
- heartbreak: betrayal, rejection, end of love, broken trust"""


def detect_mood_gemini(user_message: str) -> dict:
    from google import genai
    from google.genai import types
    import json, re

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
    
    response = client.models.generate_content(
        model=model_name,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=MOOD_SYSTEM_PROMPT,
        )
    )
    text = response.text.strip()
    # Strip any markdown code fences if present
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)


def detect_mood_openai(user_message: str) -> dict:
    from openai import OpenAI
    import json, re

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": MOOD_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3,
        max_tokens=400
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)


def detect_mood_fallback(user_message: str) -> dict:
    """Keyword-based fallback when no LLM is available."""
    msg = user_message.lower()

    mood_keywords = {
        "heartbreak": ["heartbroken", "betrayed", "cheated", "rejected", "dumped", "broken", "shattered"],
        "sadness": ["sad", "grief", "crying", "tears", "depressed", "pain", "hurt", "sorrow", "lonely feeling", "miserable"],
        "loneliness": ["alone", "lonely", "isolated", "no one", "empty", "abandoned", "left", "forgotten"],
        "love": ["love", "beloved", "missing", "miss", "affection", "romance", "heart", "darling", "yearn"],
        "rebellion": ["angry", "injustice", "protest", "unfair", "fight", "corrupt", "system", "oppressed", "revolt"],
        "patriotism": ["nation", "country", "india", "desh", "watan", "soldier", "homeland", "freedom", "sacrifice"],
        "spiritual": ["god", "divine", "prayer", "faith", "allah", "lord", "soul", "purpose", "meaning", "exist"],
        "hope": ["hope", "dream", "future", "better", "sunrise", "new", "tomorrow", "optimistic", "aspire"],
    }

    scores = {mood: 0 for mood in mood_keywords}
    for mood, words in mood_keywords.items():
        for word in words:
            if word in msg:
                scores[mood] += 1

    sorted_moods = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_moods[0][0] if sorted_moods[0][1] > 0 else "sadness"
    secondary = sorted_moods[1][0] if len(sorted_moods) > 1 else primary

    return {
        "primary_mood": primary,
        "secondary_mood": secondary,
        "emotional_keywords": user_message.split()[:4],
        "suggested_poets": ["iqbal", "sahir", "dinkar"],
        "mood_description": f"User seems to be feeling {primary}."
    }


def detect_mood(user_message: str) -> dict:
    """Main mood detection function — uses configured LLM with fallback."""
    try:
        if LLM_PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
            return detect_mood_openai(user_message)
        elif os.getenv("GOOGLE_API_KEY"):
            return detect_mood_gemini(user_message)
        else:
            return detect_mood_fallback(user_message)
    except Exception as e:
        print(f"[MoodDetector] LLM failed, using fallback. Error: {e}")
        return detect_mood_fallback(user_message)


if __name__ == "__main__":
    test_inputs = [
        "I am heartbroken and feel completely alone",
        "I feel patriotic and proud of my nation",
        "I am searching for God and the meaning of life",
        "I am angry at the injustice in this world",
        "I miss her so much it hurts"
    ]
    for inp in test_inputs:
        result = detect_mood(inp)
        print(f"\nInput: {inp}")
        print(f"Result: {result}")
