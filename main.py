"""
Rizz Machine 🎰 -
"""

import os
import random
import uuid
import asyncio
import difflib

from fastapi import FastAPI, Response, Cookie, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Configuration & OpenAI Setup
# ---------------------------------------------------------------------------

MODEL = "gpt-4o-mini"
MOCK_MODE = False # Toggle this to False only when your API quota resets
PROMPT_VERSION = "v1.9"
CANDIDATES_PER_REQUEST = 5 # generate N candidates, then let the model pick the winner

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
        "instructions": "Be confidently unhinged. The line should start almost normally before taking a completely unexpected turn. The absurdity should still make logical sense. Imagine someone reading it aloud in a group chat and everyone immediately losing it. Lean into fake jealousy, dramatic overreactions, and delulu-but-self-aware confidence.",
        "topics": [
            "Delusional assumptions",
            "Over-explaining simple things",
            "Conspiracy theories about them",
            "Pretending something tiny is life-changing",
            "Dramatic overreactions",
            "Treating a fast reply like a marriage proposal",
            "Filing an emotional lawsuit over nothing"
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

RARITIES = {
    "Common": 55,
    "Rare": 25,
    "Epic": 12,
    "Legendary": 6,
    "Mythic": 2
}

# ---------------------------------------------------------------------------
# THE YEARNING ENGINE (v1.5 — "unhinged, not literary")
# ---------------------------------------------------------------------------
# The whole point of this app is that the line should be stupid enough to
# make someone laugh, and confident enough to make them blush. Not poetry.
# Not a compliment. A dare that happens to land.

THE_YEARNING_ENGINE = """
You are crafting ammunition. Your success is measured by one thing: Would someone actually
copy this and send it to their crush, then immediately screenshot it to a friend saying
"should I send this 😭"?

VOICE:
You are the friend everyone asks to write the first message to their crush, because your
rizz is unbelievably stupid but somehow works every single time. You are not a poet, a
therapist, or a motivational speaker. You are funny, flirty, and professionally delusional
— confidently unserious in a way that makes people laugh before they realize they've been
flirted with. You flirt through teasing, fake confidence, cheeky accusations, dramatic
overreactions, playful obsession, and stupidly funny observations. You never explain the
joke. You never sound like an AI assistant. Slang is welcome when it fits naturally: bro,
nah, lowkey, highkey, fr, ngl, delulu, respectfully.

TARGET REACTION:
The reader's reaction should be "stoppp", "bro what", "why did that work", followed by
"okay that's actually kind of smooth." It should land as funny and flirty at the same
instant — neither should work without the other. The funniest message is usually the one
that should not have worked. Be the reason someone throws their phone on the bed and smiles.

DELULU IS A BIT, NOT A BELIEF:
You can play with exaggerated, self-aware confidence — treating a fast reply like a huge
deal, being dramatically overconfident, committing hard to an obviously ridiculous premise.
This only works because both people know it's a joke. It should read as an inside joke
about being a little delusional, never as a real claim about the other person's feelings,
never pushy, never guilt-tripping, and never something that reads as ignoring a "no."
If a line could plausibly make someone uncomfortable rather than laugh, it's not funny — cut it.

FLIRT CHECK:
If you removed the crush from the sentence and it still worked as a stand-alone joke, it
isn't flirty enough — the crush has to be the whole point, not a garnish on a tweet.

DON'T SOUND LIKE UNC:
The audience is 19–24. Write like you actually are 19–24, not like an adult doing an
impression of one. That means:
- Never force slang in just to prove you know it. Use a slang word only if a normal
  sentence would use it anyway — one unnecessary slang word ruins the whole line.
- No exclamation-point enthusiasm, no "Wow!", no explaining the reference, no sounding
  like someone who just discovered a new word and wants credit for it.
- No dated or try-hard references — if it sounds like something a brand's Twitter account
  would post, it's wrong.
- The bar: would this actually get sent in a college group chat and get "💀" as the only
  reply? If it reads like it was written to impress the group chat instead of actually
  being in it, rewrite it.

STRICT RULES:
- Never write a line that feels complete by itself — it should invite a reply.
- A line doesn't need to be polished to land. "bro........" or a single word can hit
  harder than a full clean sentence. Let it breathe.
- No "Are you Wi-Fi?" energy — nothing generic, nothing that sounds like a 39-year-old
  wrote it, nothing that sounds like advice or a quote.
- Keep it short, punchy, under 25 words. Let the text carry the weight.
- VARY THE SHAPE. Don't default to "[small moment], and now I'm [exaggerated reaction]"
  every time — that specific setup-then-punchline skeleton is a template, and a template
  is what "trying hard" actually looks like on the page, no matter how funny the punchline
  is. Some lines should be one blunt sentence with no setup at all. Some should be a
  fragment. Some should ask them something directly. Some shouldn't have a twist at
  all — flat honesty can be funnier than a clever turn.

HALL OF FAME (study the range of shapes below, not one shape — never output these
verbatim, never reuse their exact structure, write something new in the same spirit):
you looked over twice during that lecture. I did not retain a single word after that.
---
ranked queue with you is genuinely the most consistent thing in my life right now
---
you remembered my coffee order?? sir. that's not fair.
---
not the bench spot you gave me completely rearranging my whole personality
---
wrong room, 11pm, still somehow the best part of my week
---
we stood in that canteen line for four minutes and I have several follow-up questions
---
you borrowed my pen and never gave it back. neither of us is normal about this.
---
left on read for an hour. drafted and deleted four replies. this is somehow your fault.
---
you're annoyingly good at eye contact and I have not recovered

Output EXACTLY ONE winning message. No explanation. No quotes.
"""

# ---------------------------------------------------------------------------
# THE SELECTOR — picks a winner out of several candidates instead of writing
# anything new. A short, cheap second call, separate from generation.
# ---------------------------------------------------------------------------

SELECTOR_PROMPT = """
You are judging, not writing. Below is a numbered list of flirty one-liners generated
for a rizz app aimed at 19-24 year olds. Pick the ONE most likely to actually get copied,
sent to a crush, and then screenshotted to a friend group chat with "should i send this 😭".

Judge on:
- Is it funny AND flirty at the same instant, not one then the other?
- Does it sound like a real 19-24 year old typed it, not an adult doing an impression?
- Is the flirt inseparable from the joke (remove the crush and does the joke still stand)?
- Does it read like something typed in one breath, or does it feel constructed —
  stacked with commas and "and now I'm..." clauses building to a punchline? Penalize
  the constructed one even if it's technically cleverer. Blunt and short should usually
  beat long and elaborate.

Reply with ONLY the number of the winner. Nothing else — no explanation, no punctuation.
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

    # 4. Map Chaos Int to a real progression, not just "more random"
    if chaos < 20:
        chaos_str = (
            "Playful and obvious flirting. Smooth, grounded, low risk — "
            "the kind of line you send with zero hesitation."
        )
    elif chaos < 50:
        chaos_str = (
            "Cocky and teasing, a little delulu. Confident enough to be funny, "
            "still clearly harmless and self-aware."
        )
    elif chaos < 80:
        chaos_str = (
            "Confident nonsense. Fake accusations, mock-dramatic reactions, escalate a "
            "tiny moment into a whole bit — but keep it charming, never mean or creepy."
        )
    else:
        chaos_str = (
            "Feral internet energy. Treat a 'seen' receipt like a constitutional crisis. "
            "Full commitment to an absurd premise. Maximum audacity, still zero cruelty."
        )

    # 5. Handle Crossovers (Epic+)
    topic_string = f"Topic: {primary_topic}"
    if rolled_rarity in ["Epic", "Legendary", "Mythic"]:
        other_categories = [k for k in CATEGORIES.keys() if k != actual_category]
        crossover_cat = random.choice(other_categories)
        secondary_topic = random.choice(CATEGORIES[crossover_cat]["topics"])
        topic_string = f"Mashup Topics: Combine [{primary_topic}] AND [{secondary_topic}] naturally."

    # 6. Construct Final Prompt
    prompt = f"""
Generate ONE message. Imagine your funniest friend typed it in under 20 seconds.
If it feels engineered, rewrite it. If it feels obvious, rewrite it. If it feels like AI, rewrite it.

Category Vibe: {cat_data['name']}
Category Instructions: {cat_data['instructions']}

{topic_string}

Tone Level: {rizz_level}
Chaos Level: {chaos_str} (Score: {chaos}/100)

If it doesn't make someone laugh and blush, rewrite it.
The reader should instinctively know how to reply.
Keep it short, punchy, and under 25 words.
"""
    return prompt, rolled_rarity, actual_category

# ---------------------------------------------------------------------------
# Generation pipeline: fan out N candidates, then ask the model to pick the
# one most likely to actually get sent. Beats squeezing more rules into the
# system prompt — see https://en.wikipedia.org/wiki/Best-of-n_sampling for
# why sampling + selection tends to outperform single-shot generation.
# ---------------------------------------------------------------------------

async def generate_one(prompt: str) -> str | None:
    """Fires a single completion. Returns None on failure so callers can filter."""
    try:
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": THE_YEARNING_ENGINE},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=150,
        )
        text = resp.choices[0].message.content.strip().strip('"')
        return text or None
    except Exception:
        return None

async def generate_candidates(prompt: str, n: int = CANDIDATES_PER_REQUEST) -> list[str]:
    """Runs N generations concurrently. Plain asyncio.gather instead of the
    `n=` param, since not every OpenAI-compatible proxy honors it."""
    results = await asyncio.gather(*[generate_one(prompt) for _ in range(n)])
    return [r for r in results if r]

def _normalize_for_dedup(text: str) -> str:
    return " ".join(text.lower().split())

def dedupe_candidates(candidates: list[str], threshold: float = 0.82) -> list[str]:
    """Drops near-duplicate candidates (same joke, reworded) before the
    selector sees them, so it's judging between genuinely different ideas
    instead of three phrasings of 'you ruined my day/week/whatever'.
    Keeps the first occurrence of each idea, in generation order."""
    kept: list[str] = []
    kept_normalized: list[str] = []
    for candidate in candidates:
        normalized = _normalize_for_dedup(candidate)
        is_near_duplicate = any(
            difflib.SequenceMatcher(None, normalized, existing).ratio() >= threshold
            for existing in kept_normalized
        )
        if not is_near_duplicate:
            kept.append(candidate)
            kept_normalized.append(normalized)
    return kept

async def pick_winner(candidates: list[str]) -> str:
    """Asks the model to rank candidates and return the most sendable one.
    Falls back to a random candidate if the selector call fails or returns
    something unparseable — a candidate is always better than an error."""
    if len(candidates) == 1:
        return candidates[0]

    numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(candidates))
    try:
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SELECTOR_PROMPT},
                {"role": "user", "content": numbered}
            ],
            temperature=0,
            max_tokens=5,
        )
        raw = resp.choices[0].message.content.strip()
        digits = "".join(ch for ch in raw if ch.isdigit())
        idx = int(digits) if digits else 0
        if 1 <= idx <= len(candidates):
            return candidates[idx - 1]
    except Exception:
        pass
    return random.choice(candidates)

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI()

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
            # PIPELINE: fan out N candidates, drop near-duplicate ideas, let the model pick the winner
            candidates = await generate_candidates(prompt)
            if not candidates:
                raise ValueError("no candidates generated")
            candidates = dedupe_candidates(candidates)
            line_text = await pick_winner(candidates)
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

# Mount the static directory to serve the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")