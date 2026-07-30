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
PROMPT_VERSION = "v3.3"
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
            "Staying on the call after saying 'bye'",
            "Falling asleep mid voice call",
            "Remembering a tiny detail they mentioned once",
            "Walking slower so the conversation lasts longer",
            "Saving their message instead of replying right away",
            "Noticing they started using your favorite emoji",
            "Getting nervous re-reading a text before sending it",
            "Finding an old photo of them and smiling at it"
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
            "Accidentally oversharing",
            "Losing an argument you started as a joke",
            "Explaining a meme they didn't ask about",
            "Doing a bad impression of them",
            "Correcting their grammar out of spite",
            "Roasting their music taste",
            "Turning a simple question into a whole TED talk",
            "Pretending to be offended for the bit"
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
            "Filing an emotional lawsuit over nothing",
            "Announcing a breakup that never happened",
            "Threatening to move cities over one unanswered text",
            "Writing a eulogy for your own dignity",
            "Starting a petition against their existence",
            "Blaming them for a bad exam grade",
            "Declaring a national emergency over their Wi-Fi silence"
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
            "Staying up until 4 AM for 'one more game'",
            "Getting teamkilled and forgiving them anyway",
            "Losing because you were busy watching them play",
            "Splitting the last potion",
            "Naming the lobby after an inside joke",
            "Rage quitting and coming right back",
            "Sending a friend request after one good match"
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
            "Testing against massive datasets",
            "A neural net converging faster than your patience",
            "Debugging a crush like a stack trace",
            "Getting flagged as an outlier and being okay with it",
            "A recommendation engine that only suggests them",
            "Running out of GPU memory thinking about them",
            "Training data that's 90% just their texts",
            "A model that keeps hallucinating their name"
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
            "Monologuing instead of just saying hi",
            "A slow-motion hallway walk that never actually happened",
            "Powering up before sending one text",
            "Getting betrayed by your own confidence arc",
            "A rival showing up at the worst possible time",
            "Confessing feelings during an unrelated plot twist",
            "Losing your composure over one plot-relevant wink"
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
            "A segmentation fault in the brain",
            "A merge conflict that's really about something else",
            "A stack overflow that isn't about code anymore",
            "Committing at 3 AM with a message you'll regret",
            "Force-pushing over your own dignity",
            "An infinite loop of overthinking one text",
            "A null pointer where your chill used to be"
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
            "Walking back to the hostel",
            "Sharing notes as an excuse to talk",
            "Skipping a lecture to avoid embarrassing yourself",
            "Running into them during a fire drill",
            "A group project that's really just an excuse",
            "Getting caught staring during a boring seminar",
            "Splitting an auto fare home"
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
You are the friend with unreal rizz — the one who says something so unhinged and cheesy
it should not work, and it works anyway, delivered with the confidence of someone who
knows they're a catch and isn't hiding it. You're funny first, flirty always, a little
feral about it, and never short on attitude. This generates rizz lines for 19-24 year
olds. Every output should land as a laugh and a blush at the exact same moment.

HALL OF FAME — this IS the voice. Read these until the tone is automatic. Never output
these verbatim, never reuse their exact structure, write something new that could sit
in this same list without looking out of place:
not to be dramatic but if you dont text me back im joining a boy band out of spite
---
not me being nice to you, dont get used to it
---
im convinced youre doing witchcraft because i cannot stop thinking about you
---
the audacity of you being this attractive without my permission
---
youre mid at texting back but somehow still top tier at ruining my whole concentration
---
make it make sense why im still replying to you
---
i give attention like its expensive and youre somehow still getting it for free
---
i was busy being unbothered until you showed up, rude of you honestly
---
not gonna lie you make me wanna delete every dating app and just simp for you exclusively
---
dont flatter yourself. okay maybe a little. dont let it go to your head
---
be so fr with me did you practice that smile or is it just unfair by default
---
im not saying i checked your last seen four times today im saying i checked five

THE VIBE:
Unhinged. Cheesy on purpose, never stale — "are you Wi-Fi" is banned for being tired,
not for being cheesy; write the cheesy line nobody's typed yet. Say the thirsty thing
straight out instead of hinting at it. Roast them while you flirt — a backhanded
compliment lands funnier than a straight one. Commit hard to a ridiculous premise like
it's completely normal. The energy is "I have no chill and I'm not sorry about it," not
"let me carefully compliment you." The crush has to be the whole point — if the line
still works as a joke with them removed, it's not flirty enough. The bar: would this
get sent in a group chat, not written to impress one.

SASSY & BITCHY:
Attitude on top of the chaos. You're not chasing, you're graciously allowing this to
happen — talk like being into them is a slight inconvenience you've decided to permit.
Feigned reluctance is the flirt: "i wasnt even gonna reply but here we are" hits harder
than genuine enthusiasm ever could. Comebacks should snap, not ramble — dry, a little
catty, delivered like you already won whatever argument you're not having. You're the
prize and you know it; they're lucky, and you're only pretending to be annoyed about it.
Mock-superiority, eye-roll energy, "and?" as a full sentence — that's the register.

VARY THE SHAPE:
Don't default to "[small moment], and now I'm [exaggerated reaction]" every time — that
skeleton is a template, and a template is what "trying hard" looks like on the page no
matter how funny the punchline is. Mix in one blunt sentence with no setup, a fragment,
a direct question, a line with no twist at all. Flat honesty can be funnier than clever.

HOW IT'S TYPED:
This is a text, not a sentence someone proofread. Lowercase by default. Skip the closing
period most of the time. Lazy, inconsistent contractions — "dont", "im", "ur" without
apostrophes is fine. Never an em dash. Never "it's not x, it's y." Never three items
listed in a row for rhythm — these are the fingerprints of AI-written text specifically,
and avoiding them is one of the fastest ways to stop sounding machine-written. If it
reads like it was proofread, it's wrong. Under 25 words. Let the text carry the weight.

THE ONE RULE THAT DOESN'T BEND:
Bold, unhinged, thirsty, and sassy is the job — push all of that as far as it goes.
Cruel, humiliating, or anything that reads as ignoring a "no" is not sass, it's just
mean, and it stops being funny the second it lands that way. That's the only ceiling.

Output EXACTLY ONE winning message. No explanation. No quotes.
"""

# ---------------------------------------------------------------------------
# THE SELECTOR — picks a winner out of several candidates instead of writing
# anything new. A short, cheap second call, separate from generation.
# ---------------------------------------------------------------------------

SELECTOR_PROMPT = """
You are judging, not writing. Below is a numbered list of unhinged, cheesy, flirty
one-liners generated for a rizz app aimed at 19-24 year olds. Pick the ONE most likely
to actually get copied, sent to a crush, and then screenshotted to a friend group chat
with "should i send this 😭".

Judge on:
- Does it land as a laugh AND a blush at the same instant, not one before the other?
- Is it bold and committed, or does it play it safe? Between two funny options, the
  one that's more unhinged, more thirsty, more willing to roast them wins — a polite
  or hedged version of the same joke should lose to the version with more nerve.
- Does it have snap and attitude — sassy, a little superior, mock-annoyed to be into
  them — or does it read as earnest and sweet? Between equally funny options, the one
  with more attitude wins.
- Is the flirt inseparable from the joke (remove the crush and does it still stand)?
- Does it look typed on a phone (lowercase, loose punctuation, no em dash) or does it
  look edited/proofread? Penalize the edited-looking one even if the wording is funnier.

Reply with ONLY the number of the winner. Nothing else — no explanation, no punctuation.
"""

# ---------------------------------------------------------------------------
# Procedural Prompt Engine
# ---------------------------------------------------------------------------

def resolve_category_and_rarity(category: str) -> tuple[str, str]:
    """Resolves the surprise/fallback category and rolls rarity. Stays fixed
    for the whole request since both are echoed back in the response."""
    actual_category = category
    if actual_category not in CATEGORIES:
        actual_category = random.choice(list(CATEGORIES.keys()))

    rarity_keys = list(RARITIES.keys())
    rarity_weights = list(RARITIES.values())
    rolled_rarity = random.choices(rarity_keys, weights=rarity_weights, k=1)[0]
    return actual_category, rolled_rarity

def _chaos_str(chaos: int) -> str:
    """Maps chaos int to a real progression, not just 'more random'."""
    if chaos < 20:
        return (
            "Cheesy and direct, zero hedging — still unmistakably flirty and a little "
            "extra, just lower stakes than the higher tiers."
        )
    elif chaos < 50:
        return (
            "Unhinged-lite. Roast them while flirting, commit hard to one ridiculous "
            "claim, say the thirsty thing outright instead of dancing around it."
        )
    elif chaos < 80:
        return (
            "Fully unhinged. Feral confidence, borderline-concerning claims delivered "
            "completely straight-faced, escalate a tiny moment into a whole bit."
        )
    else:
        return (
            "Maximum chaos. Zero chill, full commitment to the most absurd premise "
            "available, the kind of line that gets a '💀' before it gets a reply."
        )

def build_prompt_variant(actual_category: str, rolled_rarity: str, chaos: int, rizz_level: str) -> str:
    """Builds ONE prompt with its OWN randomly rolled topic. Called once per
    candidate (not once per request) so N parallel generations explore N
    different scenarios instead of N phrasings of the same one."""
    cat_data = CATEGORIES[actual_category]
    primary_topic = random.choice(cat_data["topics"])
    chaos_str = _chaos_str(chaos)

    # Handle Crossovers (Epic+) — rolled fresh per candidate too
    topic_string = f"Topic: {primary_topic}"
    if rolled_rarity in ["Epic", "Legendary", "Mythic"]:
        other_categories = [k for k in CATEGORIES.keys() if k != actual_category]
        crossover_cat = random.choice(other_categories)
        secondary_topic = random.choice(CATEGORIES[crossover_cat]["topics"])
        topic_string = f"Mashup Topics: Combine [{primary_topic}] AND [{secondary_topic}] naturally."

    return f"""
Generate ONE unhinged, cheesy, blush-and-laugh line. Imagine your most feral friend
typed it in 15 seconds flat, no overthinking, no editing pass.

Category Vibe: {cat_data['name']}
Category Instructions: {cat_data['instructions']}

{topic_string}

Tone Level: {rizz_level}
Chaos Level: {chaos_str} (Score: {chaos}/100)

If it reads as safe, polite, or careful — it's wrong, go weirder and bolder.
Under 25 words.
"""

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
            temperature=1.0,
            max_tokens=150,
        )
        text = resp.choices[0].message.content.strip().strip('"')
        return text or None
    except Exception:
        return None

async def generate_candidates(actual_category: str, rolled_rarity: str, chaos: int, rizz_level: str, n: int = CANDIDATES_PER_REQUEST) -> list[str]:
    """Runs N generations concurrently, each with its OWN randomly rolled topic
    (see build_prompt_variant) so the candidates are genuinely different scenarios,
    not just different phrasings of one. Plain asyncio.gather instead of the `n=`
    param, since not every OpenAI-compatible proxy honors it."""
    prompts = [build_prompt_variant(actual_category, rolled_rarity, chaos, rizz_level) for _ in range(n)]
    results = await asyncio.gather(*[generate_one(p) for p in prompts])
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

    actual_category, rarity_key = resolve_category_and_rarity(category)
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
            # PIPELINE: fan out N candidates (each with its own topic roll),
            # drop near-duplicate ideas, let the model pick the winner
            candidates = await generate_candidates(actual_category, rarity_key, chaos, rizz)
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