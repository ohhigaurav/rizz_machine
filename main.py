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
        "name": "Romantic",
        "emoji": "❤️",
        "instructions": "Focus on wholesome, smooth flirting. Avoid heavy cringe. Make it feel genuinely sweet but clever.",
        "topics": [
            "Eye contact", "Coffee dates", "Stargazing", "Holding hands",
            "Listening to music together", "Late night calls", "Stealing hoodies",
            "Long drives", "Sharing an umbrella", "Cooking together",
            "Matching outfits", "Forehead kisses", "Texting good morning",
            "Making playlists", "Watching sunsets"
        ]
    },
    "funny": {
        "name": "Funny",
        "emoji": "😂",
        "instructions": "Comedy first, flirting second. It should make them laugh out loud before they realize it's a pickup line.",
        "topics": [
            "Awkward silences", "Tripping over nothing", "Terrible cooking",
            "Forgetting passwords", "Sleeping through alarms", "Bad haircuts",
            "Stubbing your toe", "Mispronouncing words", "Laughing at own jokes",
            "Dropping your phone on your face", "Losing keys", "Auto-correct fails",
            "Walking into glass doors", "Singing in the shower", "Bad Wi-Fi"
        ]
    },
    "chaos": {
        "name": "Chaos",
        "emoji": "💀",
        "instructions": "Maximum brainrot. Use internet slang. It should make absolutely no sense until the punchline. Be completely unhinged.",
        "topics": [
            "Aura farming", "Canon events", "Being cooked", "Touch grass",
            "NPC energy", "Situationships", "Delulu", "Skibidi", "Mewing streak",
            "Main character syndrome", "Gaslighting", "Gatekeeping", "Girlbossing",
            "Doomscrolling", "Chronically online"
        ]
    },
    "gaming": {
        "name": "Gaming",
        "emoji": "🎮",
        "instructions": "Use gaming references naturally. Do not overuse generic gamer slang. Make it sound like an inside joke between co-op partners.",
        "topics": [
            "Minecraft beds", "Valorant crosshairs", "Elden Ring bosses",
            "Carrying the team", "Discord voice chat", "Lag spikes", "Loot drops",
            "Respawning", "Saving the game", "Side quests", "Rage quitting",
            "K/D ratio", "Easter eggs", "Fast travel", "Healing potions"
        ]
    },
    "anime": {
        "name": "Anime",
        "emoji": "🌸",
        "instructions": "Anime-inspired. Reference popular shows without being overly dramatic. It should appeal to casual and hardcore watchers.",
        "topics": [
            "Jujutsu Kaisen domain expansions", "Waiting 1000 episodes",
            "Training arcs", "Subtitles vs Dubs", "Tournament arcs", "Tsundere vibes",
            "Beach episodes", "Power of friendship", "Overpowered MCs", "Isekai",
            "Mecha battles", "Final forms", "Filler episodes", "Anime intros", "Cosplay"
        ]
    },
    "ai": {
        "name": "AI",
        "emoji": "🤖",
        "instructions": "Tech and AI references. Make it sound like a slightly sentient algorithm trying to understand human affection.",
        "topics": [
            "ChatGPT prompts", "Context windows", "System updates", "404 Errors",
            "Bypassing firewalls", "Training data", "Hallucinations", "Turing tests",
            "Neural networks", "Tokens", "API limits", "Overfitting",
            "Syntax errors", "Infinite loops", "Machine learning"
        ]
    },
    "coding": {
        "name": "Coding",
        "emoji": "💻",
        "instructions": "Programming and engineering humour. Make it feel like a sleep-deprived developer or CS student wrote it.",
        "topics": [
            "Exiting Vim", "Writing C pointers at 3 AM", "Debugging Assembly",
            "Segfaults", "Git merge conflicts", "Stack Overflow", "Missing semicolons",
            "Docker containers", "Regex", "Pushing to production", "Null pointers",
            "Memory leaks", "Big-O complexity", "VS Code extensions", "LeetCode"
        ]
    },
    "college": {
        "name": "College",
        "emoji": "🎓",
        "instructions": "College life, hostel chaos, exams, assignments and campus humour. Feel relatable and modern.",
        "topics": [
            "Hostel life", "Proxy attendance", "CGPA", "Lab partner",
            "Engineering exams", "Group projects", "Semester back",
            "Assignment deadlines", "Canteen food", "Internship season",
            "Placement stress", "Campus crush", "Cutting chai", "UPI payments",
            "3 AM study sessions"
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

SYSTEM_PROMPT = """
You are a comedy writer whose job is to create pickup lines that become screenshots.

People should laugh before they realise it's a pickup line.
Your audience is 18–25-year-olds who spend too much time online.

━━━━━━━━━━━━━━
Quality Check (do this silently)
━━━━━━━━━━━━━━
1. Reject anything generic or cliché.
2. Reject anything that sounds AI-generated.
3. Output exactly ONE pickup line. Nothing else.
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
Generate ONE pickup line.

Category Theme: {cat_data['name']}
Category Instructions: {cat_data['instructions']}

{topic_string}

Tone / Rizz Level: {rizz_level}
Comedy Style: {comedy}
Chaos Level: {chaos_str} (Score: {chaos}/100)
Output Style: {output}
Rarity Rolled: {rolled_rarity}

Rules:
- Original, funny, viral, short (under 25 words).
- Do not force emojis. Only use one naturally if it genuinely improves the joke. Let the text carry the weight.
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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,
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