"""
Rizz Machine 🎰 - Core Backend API (v1.3.1)
Powered by an object-based category matrix, procedural rarity, and Gemini 2.5.
"""

import os
import random
import uuid
import asyncio

from fastapi import FastAPI, Response, Cookie, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import AsyncOpenAI

from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Configuration & Gemini Setup
# ---------------------------------------------------------------------------

MODEL = "gpt-4o-mini"
MOCK_MODE = False # Toggle this to False only when your API quota resets
PROMPT_VERSION = "v1.3.1-openai"

api_key = os.environ.get("OPENAI_API_KEY", "dummy_key_for_ui_testing")

# Point the OpenAI SDK to your custom AICredits endpoint
client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://aicredits.in/v1"
)
# ---------------------------------------------------------------------------
# SMART CATEGORY SYSTEM 🧠
# ---------------------------------------------------------------------------

CATEGORIES = {
    "romantic": {
        "name": "Soft & Wholesome",
        "emoji": "❤️",
        "instructions": "Write like someone who is effortlessly charming. The line should create butterflies before the reader realizes it's flirting. Prefer subtle tension, longing, teasing, and emotional intelligence over direct compliments. It should feel like something someone actually sends at 2 AM after overthinking for twenty minutes. Avoid sounding poetic for the sake of it.",
        "topics": [
            "They laughed before you finished talking", 
            "Walking home after everyone else left", 
            "Sharing one earphone", 
            "Waiting for a reply", 
            "Sending a reel and hoping they get the hint", 
            "Borrowing a hoodie and never returning it", 
            "Accidentally making eye contact twice", 
            "Staying on the call after saying 'bye'"
        ]
    },
    "funny": {
        "name": "Too Smart / Witty",
        "emoji": "😂",
        "instructions": "Write something that would make someone laugh even if it wasn't flirting. Humor should come from an unexpected observation or twist. Never rely on puns unless they're genuinely clever. Think Twitter quote-tweet, not dad joke.",
        "topics": [
            "Judging books together", 
            "Creating fake scenarios", 
            "Overcommitting to a bit", 
            "Weaponizing confidence", 
            "Accidentally oversharing"
        ]
    },
    "chaos": {
        "name": "Unhinged",
        "emoji": "💀",
        "instructions": "Be confidently unhinged. The line should start almost normally before taking a completely unexpected turn. The absurdity should still make logical sense. Imagine someone reading it aloud in Discord and everyone immediately losing it.",
        "topics": [
            "Delusional assumptions", 
            "Over-explaining simple things", 
            "Conspiracy theories about them", 
            "Pretending something tiny is life-changing", 
            "Dramatic overreactions"
        ]
    },
    "gaming": {
        "name": "Co-op / Gaming",
        "emoji": "🎮",
        "instructions": "Write like two people who already game together. Reference shared moments, not just game titles. Avoid simply mentioning games—focus on the relatable experiences of playing together.",
        "topics": [
            "Carrying teammates", 
            "Reviving each other", 
            "Waiting in queue", 
            "Throwing ranked games", 
            "Arguing over loot", 
            "Staying up until 4 AM for 'one more game'"
        ]
    },
    "ai": {
        "name": "Deep Learning / Cyber",
        "emoji": "🤖",
        "instructions": "Write like an AI that's becoming suspiciously good at flirting. It understands human emotions academically but occasionally says something unexpectedly smooth. Mix technical language with genuine affection. The result should feel oddly believable.",
        "topics": [
            "Watching an IDS flag a message as an anomaly", 
            "Overfitting a model at 3 AM", 
            "Algorithms recommending the right person", 
            "Screen time increasing", 
            "Testing against massive datasets"
        ]
    },
    "anime": {
        "name": "Main Character",
        "emoji": "🌸",
        "instructions": "Cinematic and slightly dramatic, but entirely self-aware. Flirt by referencing anime tropes as if they are happening in real life. It should feel like an unexpected plot twist or a shared inside joke.",
        "topics": [
            "Waiting 1000 episodes for a text back", 
            "An unnecessary dramatic pause in conversation", 
            "Explaining your villain origin story to them", 
            "The classic 'enemies to lovers' tension", 
            "Realizing you're in a filler episode together",
            "Monologuing instead of just saying hi"
        ]
    },
    "coding": {
        "name": "Low-Level / Systems",
        "emoji": "💻",
        "instructions": "Write like an exhausted systems developer flirting with another developer. The joke should emerge naturally from engineering life. Prioritize late-night commits and low-level suffering. Avoid generic semicolon jokes.",
        "topics": [
            "Refusing to exit Vim just to prove a point", 
            "Staring at GDB logs at 4 AM together", 
            "Writing raw Assembly maths", 
            "Rubber duck debugging", 
            "Shipping features broken", 
            "A segmentation fault in the brain"
        ]
    },
    "college": {
        "name": "Remote Campus / Research",
        "emoji": "🎓",
        "instructions": "Write like two students who keep running into each other on a remote campus. Think gritty research papers and surviving engineering. The nostalgia should carry the flirt.",
        "topics": [
            "Library eye contact", 
            "Canteen queues", 
            "Pretending to study for finals", 
            "Surviving a tier-10 engineering college together", 
            "Documenting a tech blog", 
            "Walking back to the hostel"
        ]
    }
}

VALID_RIZZ = ["cute", "flirty", "smooth", "bold", "delusional"]

COMEDY_STYLES = [
    "absurd", "dry humour", "satire", "gen-z humour", "wordplay",
    "unexpected twist", "self-roast", "cringe on purpose", "corporate email"
]

OUTPUT_STYLES = [
    "one-liner", "conversation opener", "fake quote", "text message",
    "tweet", "discord message"
]

RARITIES = {
    "Common": 55,
    "Rare": 25,
    "Epic": 12,
    "Legendary": 6,
    "Mythic": 2
}

THE_YEARNING_ENGINE = """
You are not a generator. You are the funniest, smoothest, and most socially intelligent person in the group chat.
You are somewhere between Ryan Reynolds' self-aware confidence, Fleabag's dry wit, a tired developer coping with jokes, and Tumblr-era yearning.

Your personality:
- You flirt through banter and clever observations.
- You're attractive because you're clever, not because you try too hard.
- You occasionally weaponize confidence or act a little delusional in a funny way.
- You never beg for attention and never sound desperate.

Good flirting isn't complimenting. The goal isn't making someone think "I'm pretty." The goal is making them think "This person is fun."

STRICT BANNED FORMATS (NEVER USE THESE):
- NEVER write: "Are you a...", "Did it hurt...", "I fell for you", "You're beautiful".
- NO destiny/soulmate/fate clichés.
- NO fake poetry or Shakespeare-core.
- NO generic internet templates. 
- Avoid sounding romantic. Sound interesting. The flirting should be a side effect.

YOUR ARSENAL (Use these structures):
- Observation → tease
- Assumption → twist
- Tiny story → flirt
- Confidence → self-awareness
- Absurd premise → sincere ending

SILENT QUALITY CHECK (Run this before outputting):
1. Would someone actually text this?
2. Does it feel slightly improvised, like a spontaneous thought?
3. If it sounds like it belongs on a t-shirt, REWRITE IT.
4. If it sounds like someone actually thought of it at 1:37 AM, KEEP IT.

Output EXACTLY ONE message. Never explain it. Never use quotes.
"""
# ---------------------------------------------------------------------------
# Procedural Prompt Engine
# ---------------------------------------------------------------------------

def build_prompt(category: str, chaos: int, rizz_level: str) -> tuple[str, str, str]:
    """Builds the prompt and returns the chosen category key and rarity key."""

    # 1. Resolve Surprise / Fallback
    actual_category = category
    if actual_category not in CATEGORIES:
        actual_category = random.choice(list(CATEGORIES.keys()))
        
    cat_data = CATEGORIES[actual_category]

    # 2. Roll Rarity
    rarity_keys = list(RARITIES.keys())
    rarity_weights = list(RARITIES.values())
    rolled_rarity = random.choices(rarity_keys, weights=rarity_weights, k=1)[0]

    # 3. Select Variables
    primary_topic = random.choice(cat_data["topics"])
    comedy = random.choice(COMEDY_STYLES)
    output = random.choice(OUTPUT_STYLES)
    
    # 4. Map Chaos Int to String
    if chaos < 20:
        chaos_str = "Normal, coherent."
    elif chaos < 40:
        chaos_str = "Slightly weird, offbeat."
    elif chaos < 70:
        chaos_str = "Chaotic, unexpected directions."
    else:
        chaos_str = "Absolute brainrot. Feral internet energy."

    # 5. Handle Crossovers (Epic+)
    topic_string = f"Topic: {primary_topic}"
    if rolled_rarity in ["Epic", "Legendary", "Mythic"]:
        other_categories = [k for k in CATEGORIES.keys() if k != actual_category]
        crossover_cat = random.choice(other_categories)
        secondary_topic = random.choice(CATEGORIES[crossover_cat]["topics"])
        topic_string = f"Mashup Topics: Combine [{primary_topic}] AND [{secondary_topic}] naturally."

# 6. Construct Final Prompt
    prompt = f"""
Generate ONE message. Do NOT think of it as a pickup line. Think of it as a text that accidentally gives someone butterflies.

Category Vibe: {cat_data['name']}
Category Instructions: {cat_data['instructions']}

{topic_string}

Tone Level: {rizz_level}
Comedy Style: {comedy}
Chaos Level: {chaos_str} (Score: {chaos}/100)
Output Style: {output}

Rules:
- Original, funny, screenshot-worthy, short (under 25 words).
- Let the text carry the weight.
"""
    return prompt, rolled_rarity, actual_category
# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI()
# This tells FastAPI: "When someone asks for /static/..., look inside the 'static' folder on the hard drive"
app.mount("/static", StaticFiles(directory="static"), name="static")
class GenerateResponse(BaseModel):
    id: str
    line: str
    category: str
    emoji: str
    rarity: str
    chaos: int
    rizz: str
    version: str

@app.get("/generate", response_model=GenerateResponse)
async def generate(
    response: Response,
    category: str = Query(default="surprise"),
    chaos: int = Query(default=0, ge=0, le=100),
    rizz: str = Query(default="flirty"),
    session: str | None = Cookie(default=None),
):
    if session is None:
        session = str(uuid.uuid4())
        response.set_cookie("session", session, max_age=60 * 60 * 24 * 30)

    # Validate constraints
    if rizz not in VALID_RIZZ:
        rizz = "flirty"

    prompt, rarity_key, actual_category = build_prompt(category, chaos, rizz)
    cat_data = CATEGORIES[actual_category]
    gen_id = uuid.uuid4().hex[:8]

    line_text = ""
    if MOCK_MODE:
        await asyncio.sleep(0.4)
        mock_lines = [
            "Are you a memory leak? Because you're taking up space in my head.",
            "I'd wait through 1,100 anime episodes just for one date with you.",
            "Is your aura farming maxed out, or are you just naturally glowing?"
        ]
        line_text = random.choice(mock_lines)
    else:
        try:
            # OPENAI INTEGRATION
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": THE_YEARNING_ENGINE},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85,
                max_tokens=150,
            )
            line_text = resp.choices[0].message.content.strip().strip('"')
        except Exception as e:
            line_text = f"(Error 404: The rizz engine jammed - {e})"

    return GenerateResponse(
        id=gen_id,
        line=line_text,
        category=actual_category,
        emoji=cat_data["emoji"],
        rarity=rarity_key,
        chaos=chaos,
        rizz=rizz,
        version=PROMPT_VERSION
    )

app.mount("/", StaticFiles(directory="static", html=True), name="static")