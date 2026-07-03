import streamlit as st
import sys
import os
import base64
import html as html_module
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from backend.mood_detector import detect_mood
from backend.rag_pipeline import get_shayari
from backend.tts_engine import synthesize_speech, get_voice_info
try:
    from backend.add_shayari import add_shayari, delete_shayari, get_all_shayaris, get_db_stats, VALID_MOODS
    ADMIN_AVAILABLE = True
except Exception:
    ADMIN_AVAILABLE = False

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShayariBot — Poetry for Your Soul",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={"About": "ShayariBot — A mood-based RAG shayari engine featuring Iqbal, Sahir & Dinkar"}
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Noto+Nastaliq+Urdu&display=swap');

/* === Root Variables === */
:root {
    --bg-primary: #121217;
    --bg-card: #181822;
    --bg-glass: rgba(255,255,255,0.06);
    --border-glow: rgba(212,175,55,0.2);
    --gold: #d4af37;
    --gold-light: #f4d97d;
    --gold-dim: rgba(212,175,55,0.12);
    --text-primary: #f5f2eb;
    --text-secondary: #a8a496;
    --text-muted: #6e6b63;
    --iqbal-color: #a78bfa;
    --sahir-color: #f472b6;
    --dinkar-color: #fb923c;
    --iqbal-glow: rgba(167,139,250,0.25);
    --sahir-glow: rgba(244,114,182,0.25);
    --dinkar-glow: rgba(251,146,60,0.25);
}

/* === Base Styles === */
.stApp {
    background: var(--bg-primary);
    background-image:
        radial-gradient(ellipse at 20% 10%, rgba(167,139,250,0.05) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 90%, rgba(212,175,55,0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(244,114,182,0.03) 0%, transparent 70%);
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}

/* Hide default Streamlit header */
header[data-testid="stHeader"] { display: none; }
.stDeployButton { display: none; }

/* === Hero Header === */
.hero-header {
    text-align: center;
    padding: 3rem 1rem 2rem;
    position: relative;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.2rem, 5vw, 3.5rem);
    font-weight: 700;
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 50%, #b8860b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.1;
}
.hero-tagline {
    font-size: 1rem;
    color: var(--text-secondary);
    margin-top: 0.75rem;
    font-style: italic;
    letter-spacing: 0.05em;
}
.hero-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin: 1.5rem auto;
    max-width: 400px;
}
.hero-divider::before, .hero-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--gold), transparent);
}
.hero-divider span {
    color: var(--gold);
    font-size: 1.2rem;
}

/* === Poet Pills === */
.poet-pills {
    display: flex;
    gap: 0.6rem;
    justify-content: center;
    flex-wrap: wrap;
    margin: 1rem 0 2rem;
}
.poet-pill {
    padding: 0.4rem 1.1rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    border: 1px solid;
}
.pill-iqbal {
    color: var(--iqbal-color);
    border-color: var(--iqbal-color);
    background: var(--iqbal-glow);
}
.pill-sahir {
    color: var(--sahir-color);
    border-color: var(--sahir-color);
    background: var(--sahir-glow);
}
.pill-dinkar {
    color: var(--dinkar-color);
    border-color: var(--dinkar-color);
    background: var(--dinkar-glow);
}

/* === Input Section === */
.input-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* Streamlit text input override */
.stTextInput input {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-glow) !important;
    border-radius: 20px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.05rem !important;
    padding: 1.4rem 1.6rem !important;
    line-height: 1.7 !important;
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    backdrop-filter: blur(10px) !important;
}
.stTextInput input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-dim), 0 12px 40px rgba(212,175,55,0.12) !important;
    outline: none !important;
    transform: translateY(-2px) !important;
}
.stTextInput input::placeholder { color: var(--text-muted) !important; }

/* === Primary Button === */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #d4af37 0%, #f4d97d 50%, #c9991a 100%) !important;
    color: #121217 !important;
    border: none !important;
    border-radius: 18px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.05em !important;
    padding: 1rem 2rem !important;
    cursor: pointer !important;
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 8px 32px rgba(212,175,55,0.25) !important;
    text-transform: uppercase !important;
}
.stButton > button:hover {
    transform: translateY(-3px) scale(1.01) !important;
    box-shadow: 0 12px 48px rgba(212,175,55,0.4) !important;
    filter: brightness(1.1) !important;
}
.stButton > button:active { transform: translateY(1px) scale(0.98) !important; }

/* === Mood Badge === */
.mood-display {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--bg-glass);
    border: 1px solid var(--border-glow);
    border-radius: 12px;
    padding: 0.9rem 1.4rem;
    margin: 1.5rem 0;
    backdrop-filter: blur(10px);
}
.mood-icon { font-size: 1.6rem; }
.mood-text-block { flex: 1; }
.mood-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}
.mood-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--gold);
    text-transform: capitalize;
}
.mood-desc {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-top: 0.2rem;
    font-style: italic;
}

/* === Shayari Card === */
.shayari-card {
    background: var(--bg-card);
    border: 1px solid var(--border-glow);
    border-radius: 28px;
    padding: 2.8rem 2.5rem;
    margin: 2rem 0;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.7s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
    box-shadow: 0 16px 50px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.05);
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.shayari-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 24px 70px rgba(0,0,0,0.4), inset 0 1px 1px rgba(255,255,255,0.08);
}
.shayari-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 28px 28px 0 0;
}
.shayari-card.poet-iqbal::before { background: linear-gradient(90deg, var(--iqbal-color), transparent); }
.shayari-card.poet-sahir::before { background: linear-gradient(90deg, var(--sahir-color), transparent); }
.shayari-card.poet-dinkar::before { background: linear-gradient(90deg, var(--dinkar-color), transparent); }

.shayari-card::after {
    content: '"';
    position: absolute;
    top: 1rem; right: 2rem;
    font-family: 'Playfair Display', serif;
    font-size: 8rem;
    line-height: 1;
    opacity: 0.04;
    color: var(--gold);
    pointer-events: none;
}

/* Poet header within card */
.card-poet-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.8rem;
}
.poet-avatar {
    width: 48px; height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    flex-shrink: 0;
}
.avatar-iqbal { background: var(--iqbal-glow); border: 1px solid var(--iqbal-color); }
.avatar-sahir { background: var(--sahir-glow); border: 1px solid var(--sahir-color); }
.avatar-dinkar { background: var(--dinkar-glow); border: 1px solid var(--dinkar-color); }

.poet-name {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.01em;
}
.name-iqbal { color: var(--iqbal-color); }
.name-sahir { color: var(--sahir-color); }
.name-dinkar { color: var(--dinkar-color); }

.poet-collection {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 0.1rem;
}
.poet-title {
    font-size: 0.88rem;
    color: var(--text-secondary);
    font-style: italic;
}

/* Shayari text */
.shayari-original {
    font-family: 'Noto Nastaliq Urdu', 'Playfair Display', serif;
    font-size: clamp(1.1rem, 2.5vw, 1.4rem);
    line-height: 2.2;
    color: var(--text-primary);
    direction: rtl;
    text-align: right;
    margin-bottom: 1.5rem;
    padding: 1.2rem 1.5rem;
    background: rgba(255,255,255,0.02);
    border-radius: 12px;
    border-right: 3px solid;
}
.shayari-original.hindi {
    direction: ltr;
    text-align: left;
    border-right: none;
    border-left: 3px solid;
    font-family: 'Playfair Display', serif;
}
.border-iqbal { border-color: var(--iqbal-color) !important; }
.border-sahir { border-color: var(--sahir-color) !important; }
.border-dinkar { border-color: var(--dinkar-color) !important; }

.shayari-transliteration {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1rem;
    color: var(--text-secondary);
    line-height: 1.9;
    margin-bottom: 1.2rem;
    padding: 0 0.5rem;
}
.shayari-translation {
    font-size: 0.88rem;
    color: var(--text-muted);
    line-height: 1.7;
    padding: 0.8rem 1rem;
    background: rgba(255,255,255,0.015);
    border-radius: 8px;
    border-left: 2px solid var(--border-glow);
    font-style: italic;
}
.shayari-translation-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin-bottom: 0.3rem;
    font-style: normal;
}

/* Context / Why This Shayari */
.context-block {
    background: var(--gold-dim);
    border: 1px solid var(--border-glow);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin: 1.5rem 0;
    animation: fadeInUp 0.8s ease 0.2s both;
}
.context-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}
.context-icon { font-size: 1rem; }
.context-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--gold);
    text-transform: uppercase;
    letter-spacing: 0.12em;
}
.context-text {
    font-size: 0.92rem;
    color: var(--text-secondary);
    line-height: 1.75;
    font-style: italic;
}

/* === Audio Player === */
.audio-section {
    margin: 1.5rem 0;
    animation: fadeInUp 0.8s ease 0.4s both;
}
.audio-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}
.audio-label-text {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.voice-badge {
    font-size: 0.7rem;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-weight: 600;
}
.badge-iqbal { background: var(--iqbal-glow); color: var(--iqbal-color); }
.badge-sahir { background: var(--sahir-glow); color: var(--sahir-color); }
.badge-dinkar { background: var(--dinkar-glow); color: var(--dinkar-color); }

/* Streamlit audio player override */
.stAudio { border-radius: 12px !important; }
.stAudio > audio {
    width: 100% !important;
    border-radius: 12px !important;
    filter: invert(0.1) !important;
}

/* === Sidebar === */
section[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border-glow) !important;
}
section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

.sidebar-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 1.5rem 0 0.75rem;
}
.poet-bio-card {
    background: var(--bg-glass);
    border: 1px solid var(--border-glow);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}
.poet-bio-name {
    font-weight: 700;
    font-size: 0.9rem;
    margin-bottom: 0.4rem;
}
.poet-bio-text {
    font-size: 0.78rem;
    color: var(--text-secondary);
    line-height: 1.6;
}

/* History item */
.history-item {
    background: var(--bg-glass);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
}
.history-item:hover { border-color: var(--border-glow); }
.history-query {
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-style: italic;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.history-poet {
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 0.3rem;
}

/* === Mood Quick Prompts === */
.mood-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0.75rem 0;
}
.mood-chip {
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    background: var(--bg-glass);
    border: 1px solid rgba(255,255,255,0.08);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
}
.mood-chip:hover { border-color: var(--gold); color: var(--gold); }

/* === Animations === */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
@keyframes pulse-gold {
    0%, 100% { box-shadow: 0 0 0 0 var(--gold-dim); }
    50% { box-shadow: 0 0 0 12px transparent; }
}

/* Loading shimmer */
.loading-pulse {
    background: linear-gradient(90deg, var(--bg-card) 25%, rgba(212,175,55,0.08) 50%, var(--bg-card) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 12px;
    height: 200px;
}

/* === Footer === */
.app-footer {
    text-align: center;
    padding: 2rem 1rem;
    margin-top: 2rem;
    color: var(--text-muted);
    font-size: 0.78rem;
    border-top: 1px solid rgba(255,255,255,0.04);
}
.footer-credit {
    color: var(--gold);
    font-weight: 600;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-glow); border-radius: 4px; }

/* Selectbox & expander */
.stSelectbox > div > div {
    background: var(--bg-glass) !important;
    border-color: var(--border-glow) !important;
    color: var(--text-primary) !important;
}
.streamlit-expanderHeader {
    background: var(--bg-glass) !important;
    border-color: var(--border-glow) !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--gold) !important; }
</style>
""", unsafe_allow_html=True)

# ── Poet Metadata ────────────────────────────────────────────────────────────
POET_META = {
    "iqbal": {
        "emoji": "🦅",
        "display": "Allama Iqbal",
        "color_class": "iqbal",
        "bio": "Philosopher-poet of the East (1877–1938). His Urdu and Persian poetry explores selfhood (Khudi), spiritual awakening, and the destiny of Muslim civilization. His most iconic works include Bang-e-Dra, Bal-e-Jibreel, and the national anthem of Pakistan.",
        "style": "Philosophical, spiritual, deeply rooted in Islamic mysticism and Western philosophy.",
        "famous": "Sitaron se aage jahan aur bhi hain..."
    },
    "sahir": {
        "emoji": "🌙",
        "display": "Sahir Ludhianvi",
        "color_class": "sahir",
        "bio": "Voice of the brokenhearted (1921–1980). A progressive Urdu poet and Bollywood lyricist whose work resonates with themes of unrequited love, social injustice, and anti-war sentiment. Known for Talkhiyaan and timeless film lyrics.",
        "style": "Melancholic, lyrical, socially conscious, deeply romantic yet disillusioned.",
        "famous": "Kabhi kabhi mere dil mein khayal aata hai..."
    },
    "dinkar": {
        "emoji": "🔥",
        "display": "Ramdhari Singh Dinkar",
        "color_class": "dinkar",
        "bio": "The Poet of Veer Ras (1908–1974). Considered the poet of national awakening, his Hindi poetry burns with patriotism, valor, and the call to righteous action. His epic Rashmirathi and Kurukshetra are landmarks of modern Hindi literature.",
        "style": "Powerful, nationalistic, warrior-spirited, rooted in the Mahabharata tradition.",
        "famous": "Singhasan khaali karo ki janta aati hai..."
    }
}

MOOD_ICONS = {
    "sadness": "💧",
    "love": "❤️",
    "loneliness": "🌑",
    "patriotism": "🏔️",
    "rebellion": "⚡",
    "spiritual": "✨",
    "hope": "🌅",
    "heartbreak": "💔",
}

MOOD_PROMPTS = [
    ("💔 Heartbroken", "I am heartbroken and feel like everything has fallen apart"),
    ("💧 Deeply Sad", "I feel a deep sadness that I cannot explain"),
    ("🌑 Lonely", "I feel completely alone and disconnected from everything"),
    ("❤️ In Love", "I am deeply in love and missing someone"),
    ("⚡ Angry & Rebellious", "I am angry at the injustice around me"),
    ("🏔️ Patriotic", "I feel deep love and pride for my nation"),
    ("✨ Seeking God", "I am searching for meaning, God, and peace"),
    ("🌅 Hopeful", "I feel hopeful about tomorrow despite everything"),
]

# ── Session State ────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "trigger_search" not in st.session_state:
    st.session_state.trigger_search = False


# ── Helper Functions ─────────────────────────────────────────────────────────
def audio_to_base64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")


def render_audio_player(audio_bytes: bytes, poet_key: str):
    b64 = audio_to_base64(audio_bytes)
    voice_info = get_voice_info(poet_key)
    badge_class = f"badge-{poet_key}"
    st.markdown(f"""
    <div class="audio-section">
        <div class="audio-label">
            <span>🎙️</span>
            <span class="audio-label-text">Listen</span>
            <span class="voice-badge {badge_class}">{voice_info.get('voice_name', voice_info.get('name'))} · {voice_info['description']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)


def render_shayari_card(result: dict):
    poet_key = result["poet_key"]
    poet_info = POET_META[poet_key]
    color_class = poet_info["color_class"]
    lang = result.get("language", "urdu")
    is_hindi = lang == "hindi"
    direction_class = "hindi" if is_hindi else ""
    original_class = f"shayari-original {direction_class} border-{color_class}".strip()
    # Convert newlines to <br> for HTML display
    shayari_lines = html_module.escape(result["shayari"]).replace("\n", "<br>")
    translit_lines = html_module.escape(result["transliteration"]).replace("\n", "<br>")
    translation = html_module.escape(result.get("translation", ""))
    title = html_module.escape(result.get('title', ''))
    collection = html_module.escape(result.get('collection', ''))
    poet_display = html_module.escape(poet_info['display'])
    translit_div = (
        f'<div class="shayari-transliteration">{translit_lines}</div>'
        if not is_hindi else ""
    )
    st.markdown(
        f'<div class="shayari-card poet-{color_class}">'
        f'<div class="card-poet-header">'
        f'<div class="poet-avatar avatar-{color_class}">{poet_info["emoji"]}</div>'
        f'<div>'
        f'<div class="poet-name name-{color_class}">{poet_display}</div>'
        f'<div class="poet-title">{title}</div>'
        f'<div class="poet-collection">📖 {collection}</div>'
        f'</div>'
        f'</div>'
        f'<div class="{original_class}">{shayari_lines}</div>'
        f'{translit_div}'
        f'<div class="shayari-translation">'
        f'<div class="shayari-translation-label">English Translation</div>'
        f'{translation}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_context(context_text: str):
    safe_text = html_module.escape(context_text)
    st.markdown(
        f'<div class="context-block">'
        f'<div class="context-header">'
        f'<span class="context-icon">🪔</span>'
        f'<span class="context-label">Why this shayari speaks to your heart</span>'
        f'</div>'
        f'<div class="context-text">{safe_text}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_mood_badge(mood_data: dict):
    mood = mood_data.get("primary_mood", "unknown")
    secondary = mood_data.get("secondary_mood", mood)
    icon = MOOD_ICONS.get(mood, "🌀")
    desc = html_module.escape(mood_data.get("mood_description", ""))
    keywords = html_module.escape(", ".join(mood_data.get("emotional_keywords", [])[:3]))
    st.markdown(
        f'<div class="mood-display">'
        f'<span class="mood-icon">{icon}</span>'
        f'<div class="mood-text-block">'
        f'<div class="mood-label">Detected Mood</div>'
        f'<div class="mood-value">{mood.title()} · {secondary.title()}</div>'
        f'<div class="mood-desc">{desc}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div class="mood-label">Keywords</div>'
        f'<div style="font-size:0.78rem;color:var(--text-muted);font-style:italic">{keywords}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem">
        <div style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;
            background:linear-gradient(135deg,#d4af37,#f0d060);-webkit-background-clip:text;
            -webkit-text-fill-color:transparent;background-clip:text;">
            ShayariBot
        </div>
        <div style="font-size:0.72rem;color:#5a5750;margin-top:0.3rem;letter-spacing:0.08em;">
            POETRY FOR YOUR SOUL
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">The Poets</div>', unsafe_allow_html=True)

    for key, meta in POET_META.items():
        color_map = {"iqbal": "#8b5cf6", "sahir": "#ec4899", "dinkar": "#f97316"}
        color = color_map[key]
        with st.expander(f"{meta['emoji']} {meta['display']}", expanded=False):
            st.markdown(f"""
            <div style="font-size:0.79rem;color:#9e9b8e;line-height:1.65;">{meta['bio']}</div>
            <div style="margin-top:0.75rem;padding:0.6rem 0.8rem;background:rgba(255,255,255,0.04);
                border-radius:8px;border-left:2px solid {color};">
                <div style="font-size:0.68rem;color:#5a5750;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:600;">Style</div>
                <div style="font-size:0.78rem;color:#9e9b8e;margin-top:0.2rem;font-style:italic;">
                    {meta['style']}
                </div>
            </div>
            <div style="margin-top:0.6rem;font-size:0.75rem;color:{color};font-style:italic;
                font-family:'Playfair Display',serif;">
                "{meta['famous']}"
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown('<div class="sidebar-section-title">Recent Sessions</div>', unsafe_allow_html=True)
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            poet_key = h["result"]["poet_key"]
            color_map = {"iqbal": "#8b5cf6", "sahir": "#ec4899", "dinkar": "#f97316"}
            color = color_map.get(poet_key, "#d4af37")
            st.markdown(f"""
            <div class="history-item">
                <div class="history-query">"{h['query']}"</div>
                <div class="history-poet" style="color:{color}">
                    {POET_META[poet_key]['emoji']} {POET_META[poet_key]['display']}
                    · {h['result']['title']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">Settings</div>', unsafe_allow_html=True)
    tts_enabled = st.toggle("🎙️ Enable Voice (TTS)", value=True,
                            help="Generates voice locally using Coqui TTS")
    show_translation = st.toggle("🔤 Show Translation", value=True)


# ── Main UI ───────────────────────────────────────────────────────────────────

# Hero Header
st.markdown("""
<div class="hero-header">
    <h1 class="hero-title">شایری بوٹ · ShayariBot</h1>
    <p class="hero-tagline">Tell me how you feel. I'll find the verse that speaks your silence.</p>
    <div class="hero-divider"><span>✦</span></div>
    <div class="poet-pills">
        <span class="poet-pill pill-iqbal">🦅 Allama Iqbal</span>
        <span class="poet-pill pill-sahir">🌙 Sahir Ludhianvi</span>
        <span class="poet-pill pill-dinkar">🔥 Ramdhari Singh Dinkar</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick mood chips (clickable presets)
st.markdown('<div class="input-label">Quick Moods — or write your own below</div>', unsafe_allow_html=True)
chip_cols = st.columns(4)
for idx, (label, prompt) in enumerate(MOOD_PROMPTS):
    with chip_cols[idx % 4]:
        if st.button(label, key=f"chip_{idx}", use_container_width=True,
                     help=f'"{prompt}"'):
            st.session_state.input_text = prompt
            st.session_state.trigger_search = True
            st.rerun()

# Main input
def on_enter_press():
    st.session_state.input_text = st.session_state.user_input_area
    st.session_state.trigger_search = True

st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
user_input = st.text_input(
    label="Your feeling",
    label_visibility="collapsed",
    value=st.session_state.input_text,
    placeholder="Share what's in your heart... 'I feel heartbroken and alone' · 'मुझे अपने देश से प्यार है' · 'میں خدا کو ڈھونڈ رہا ہوں'",
    key="user_input_area",
    on_change=on_enter_press
)

col_btn1, col_btn2 = st.columns([3, 1])
with col_btn1:
    find_btn = st.button("🎙️ Find My Shayari", use_container_width=True, type="primary")
with col_btn2:
    clear_btn = st.button("✕ Clear", use_container_width=True)

if clear_btn:
    st.session_state.input_text = ""
    st.session_state.current_result = None
    st.rerun()

if st.session_state.get("trigger_search"):
    find_btn = True
    st.session_state.trigger_search = False

# ── Processing ────────────────────────────────────────────────────────────────
if find_btn and user_input.strip():
    with st.container():
        with st.spinner(""):
            st.markdown("""
            <div style="text-align:center;padding:2rem;color:#9e9b8e;font-style:italic;font-size:0.9rem;
                animation:fadeInUp 0.4s ease;">
                🎙️ Reading your emotions... finding the perfect verse...
            </div>
            """, unsafe_allow_html=True)

            # Step 1: Detect mood
            mood_data = detect_mood(user_input.strip())

            # Step 2: RAG retrieval + context
            result = get_shayari(user_input.strip(), mood_data)

            if result:
                # Step 3: Save to state and trigger audio generation in the render section
                st.session_state.current_result = {
                    "result": result,
                    "mood_data": mood_data,
                    "audio_bytes": None,
                    "needs_audio": tts_enabled,
                }
                st.session_state.history.append({
                    "query": user_input.strip(),
                    "result": result,
                    "mood_data": mood_data,
                })
                st.session_state.input_text = user_input.strip()
                st.rerun()
            else:
                st.error("⚠️ Could not retrieve a shayari. Please check that ChromaDB is initialized by running `python backend/ingest.py`")

elif find_btn and not user_input.strip():
    st.warning("Please share how you're feeling...")

# ── Result Display ────────────────────────────────────────────────────────────
if st.session_state.current_result:
    r = st.session_state.current_result
    result = r["result"]
    mood_data = r["mood_data"]
    audio_bytes = r.get("audio_bytes")

    # Mood badge
    render_mood_badge(mood_data)

    # Shayari card
    render_shayari_card(result)

    # Context / why this shayari
    if result.get("why_this_shayari"):
        render_context(result["why_this_shayari"])

    # Handle Audio AFTER rendering text
    if r.get("needs_audio"):
        if result["poet_key"] == "iqbal":
            st.session_state.current_result["audio_bytes"] = None
            st.session_state.current_result["needs_audio"] = False
            st.session_state.current_result["audio_unavailable"] = True
            st.rerun()
        else:
            with st.spinner("🎙️ Cloning voice and generating audio... (This may take a minute)"):
                audio_bytes = synthesize_speech(result)
                st.session_state.current_result["audio_bytes"] = audio_bytes
                st.session_state.current_result["needs_audio"] = False
                st.rerun()

    # Audio Player
    if r.get("audio_bytes"):
        render_audio_player(r.get("audio_bytes"), result["poet_key"])
    elif r.get("audio_unavailable"):
        st.markdown("""
        <div style="padding:0.8rem 1rem;background:rgba(212,175,55,0.08);
            border:1px solid rgba(212,175,55,0.2);border-radius:10px;
            font-size:0.82rem;color:#9e9b8e;">
            🎙️ <strong style="color:#d4af37;">Voice unavailable</strong> —
            Audio generation is not available for Allama Iqbal at this time.
        </div>
        """, unsafe_allow_html=True)
    elif tts_enabled and r.get("audio_bytes") is None and not r.get("needs_audio"):
        st.markdown("""
        <div style="padding:0.8rem 1rem;background:rgba(212,175,55,0.08);
            border:1px solid rgba(212,175,55,0.2);border-radius:10px;
            font-size:0.82rem;color:#9e9b8e;">
            🎙️ <strong style="color:#d4af37;">Voice unavailable</strong> —
            The AI could not generate the voice. Check the terminal for errors.
        </div>
        """, unsafe_allow_html=True)

    # Metadata tags
    mood_tags = result.get("mood_tags", [])
    tags_html = " ".join([
        f'<span style="padding:0.2rem 0.6rem;background:rgba(255,255,255,0.05);'
        f'border-radius:999px;font-size:0.72rem;color:#5a5750;border:1px solid rgba(255,255,255,0.06);">'
        f'#{t}</span>'
        for t in mood_tags
    ])
    st.markdown(f"""
    <div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-top:1rem;align-items:center">
        <span style="font-size:0.7rem;color:#5a5750;text-transform:uppercase;
            letter-spacing:0.1em;font-weight:600;">Themes:</span>
        {tags_html}
        <span style="margin-left:auto;font-size:0.7rem;color:#5a5750;font-style:italic;">
            Match score: {result.get('match_score', '')}
        </span>
    </div>
    """, unsafe_allow_html=True)

# ── Admin Panel ────────────────────────────────────────────────────────────
st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)



# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
    Built with <span class="footer-credit">❤️</span> By <span class="footer-credit">Ali Asad Quasim</span>·
    Poetry by <span class="footer-credit">Iqbal, Sahir & Dinkar</span><br>
    <span style="color:#3a3830">ShayariBot © 2026 — For the soul that seeks</span>
</div>
""", unsafe_allow_html=True)
