"""
content_calendar.py — Determines today's content type and topic.

Weekly schedule:
  Monday    → learning video
  Tuesday   → kids song
  Wednesday → learning video
  Thursday  → movement & dance
  Friday    → kids song
  Saturday  → story time
  Sunday    → movement & dance
  DAILY     → YouTube Short clipped from main video

Topic pools rotate so the same topic never repeats on consecutive same-weekdays.
Seasonal overrides apply for major holidays.
"""

import json
import os
from datetime import date, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Topic pools — rotated per weekday independently
# ---------------------------------------------------------------------------

LEARNING_TOPICS = [
    "colors", "numbers 1-10", "shapes", "alphabet A-Z",
    "animals on the farm", "wild animals", "ocean creatures",
    "emotions", "body parts", "fruits", "vegetables",
    "weather", "seasons", "days of the week", "months of the year",
    "opposites", "transport vehicles", "clothes",
]

SONG_TOPICS = [
    "a happy morning song", "a bedtime lullaby", "a friendship song",
    "a counting song", "a rainbow colors song", "a funny animal song",
    "a dancing teddy bears song", "a bath time song", "a sharing song",
    "a superhero kids song",
]

MOVEMENT_TOPICS = [
    "jumping like frogs", "flying like butterflies", "stretching like cats",
    "marching like soldiers", "swimming like fish", "stomping like elephants",
    "spinning like tops", "tiptoeing like fairies",
]

STORY_TOPICS = [
    "a brave little mouse", "the magical rainbow", "the lost puppy",
    "the cloud who learned to rain", "three little stars",
    "the kind dragon", "the sneezing elephant", "the tiny seed that grew",
]

# ---------------------------------------------------------------------------
# Seasonal / holiday overrides
# Map (month, day) → override for each content type key that applies
# ---------------------------------------------------------------------------

SEASONAL_OVERRIDES: dict[tuple[int, int], dict] = {
    (12, 24): {"topic": "Christmas Eve adventure", "theme": "christmas"},
    (12, 25): {"topic": "Christmas Day celebration", "theme": "christmas"},
    (10, 31): {"topic": "friendly Halloween costumes", "theme": "halloween"},
    (2, 14): {"topic": "Valentine's Day love and hearts", "theme": "valentines"},
    (1, 1):  {"topic": "Happy New Year celebration", "theme": "new_year"},
    (3, 17): {"topic": "St. Patrick's Day lucky shamrocks", "theme": "st_patricks"},
    (4, 1):  {"topic": "April Fools fun surprises", "theme": "april_fools"},
}

# Map weekday int (0=Mon…6=Sun) → (content_type, topic_pool)
WEEKDAY_SCHEDULE = {
    0: ("learning", LEARNING_TOPICS),
    1: ("song", SONG_TOPICS),
    2: ("learning", LEARNING_TOPICS),
    3: ("movement", MOVEMENT_TOPICS),
    4: ("song", SONG_TOPICS),
    5: ("story", STORY_TOPICS),
    6: ("movement", MOVEMENT_TOPICS),
}

# State file to track which index in each pool we're at
_STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "calendar_state.json")


def _load_state() -> dict:
    if os.path.exists(_STATE_FILE):
        with open(_STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
    with open(_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _next_topic(pool: list[str], pool_key: str, state: dict) -> tuple[str, dict]:
    """Return the next topic from a pool (rotating), updating state."""
    idx = state.get(pool_key, 0)
    topic = pool[idx % len(pool)]
    state[pool_key] = (idx + 1) % len(pool)
    return topic, state


def _seasonal_override(today: date) -> Optional[dict]:
    return SEASONAL_OVERRIDES.get((today.month, today.day))


def get_todays_content(today: Optional[date] = None) -> dict:
    """
    Returns a dict with keys:
      type        — 'learning' | 'song' | 'movement' | 'story'
      topic       — string topic / theme
      short       — True (always include a Short)
      theme       — optional seasonal theme string
      date        — ISO date string
    """
    if today is None:
        today = date.today()

    weekday = today.weekday()  # 0 = Monday
    content_type, pool = WEEKDAY_SCHEDULE[weekday]
    pool_key = f"{content_type}_{weekday}"

    state = _load_state()
    topic, state = _next_topic(pool, pool_key, state)
    _save_state(state)

    result = {
        "type": content_type,
        "topic": topic,
        "short": True,
        "theme": None,
        "date": today.isoformat(),
    }

    # Apply seasonal override if today matches
    override = _seasonal_override(today)
    if override:
        result["topic"] = override["topic"]
        result["theme"] = override.get("theme")

    return result
