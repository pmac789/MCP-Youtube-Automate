"""
claude_writer.py — Calls Claude API to write song lyrics, video script, and YouTube metadata.

Returns a dict with:
  title, description, tags, lyrics, script, short_hook, style, mood
"""

import json
import os
import logging
from typing import Optional

import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODEL = "claude-opus-4-5"

# ---------------------------------------------------------------------------
# Prompt templates per content type
# ---------------------------------------------------------------------------

_BASE_INSTRUCTIONS = """
You are a children's content creator for the YouTube channel "Happy Melody Kids",
aimed at ages 1–6. All content must be:
- Cheerful, safe, age-appropriate, and educational where possible
- Simple vocabulary; short sentences; repetition welcomed
- Never scary, violent, or adult in any way
- Rhyming lyrics where applicable
- Visually imaginative with [VISUAL: ...] stage directions every 3-4 lines

Respond ONLY with a valid JSON object — no markdown fences, no extra text.
"""

PROMPTS: dict[str, str] = {
    "learning": """
{base}

Content type: LEARNING VIDEO
Topic: {topic}
{theme_note}

Write a fun, educational script that teaches children about "{topic}".
Return JSON with these exact keys:
{{
  "title": "YouTube title (max 60 chars, catchy, keyword-rich)",
  "description": "YouTube description (3-4 sentences, include keywords, end with subscribe CTA)",
  "tags": ["tag1", "tag2", ...],  // 10-15 tags
  "lyrics": "Song lyrics (2-3 verses + chorus, repeating chorus, total ~200 words)",
  "script": "Full video narration including song lyrics, with [VISUAL: ...] markers every 3-4 lines (~400 words)",
  "short_hook": "First 15 seconds hook line for the YouTube Short",
  "style": "Musical style for Suno (e.g. 'upbeat children\\'s pop, xylophone, claps')",
  "mood": "One-word mood (e.g. 'playful')"
}}
""",

    "song": """
{base}

Content type: KIDS SONG
Topic: {topic}
{theme_note}

Write a catchy, singalong kids song about "{topic}".
Return JSON with these exact keys:
{{
  "title": "YouTube title (max 60 chars)",
  "description": "YouTube description (3-4 sentences, include keywords, end with subscribe CTA)",
  "tags": ["tag1", "tag2", ...],
  "lyrics": "Full song lyrics (3 verses + catchy chorus, ~220 words, lots of repetition)",
  "script": "Full video script with lyrics + [VISUAL: ...] stage directions every 3-4 lines (~450 words)",
  "short_hook": "First 15 seconds hook for YouTube Short",
  "style": "Suno style string (e.g. 'fun children\\'s pop, acoustic guitar, hand claps')",
  "mood": "One-word mood"
}}
""",

    "movement": """
{base}

Content type: MOVEMENT & DANCE VIDEO
Topic: {topic}
{theme_note}

Create an energetic movement/dance video script encouraging kids to move their bodies.
Return JSON with these exact keys:
{{
  "title": "YouTube title (max 60 chars)",
  "description": "YouTube description (3-4 sentences, include keywords, end with subscribe CTA)",
  "tags": ["tag1", "tag2", ...],
  "lyrics": "Chant or song lyrics encouraging specific movements (~180 words)",
  "script": "Full video script with instructions like 'Now jump! Now spin!' + [VISUAL: ...] every 3-4 lines (~400 words)",
  "short_hook": "First 15 seconds hook for YouTube Short",
  "style": "Suno style (e.g. 'energetic children\\'s dance, drums, fun beats')",
  "mood": "One-word mood"
}}
""",

    "story": """
{base}

Content type: STORY TIME
Topic: {topic}
{theme_note}

Write a gentle, imaginative bedtime or daytime story for ages 1-6.
Return JSON with these exact keys:
{{
  "title": "YouTube title (max 60 chars)",
  "description": "YouTube description (3-4 sentences, include keywords, end with subscribe CTA)",
  "tags": ["tag1", "tag2", ...],
  "lyrics": "A short rhyming poem intro/outro for the story (~100 words)",
  "script": "Full narrated story with [VISUAL: ...] directions every 3-4 sentences (~500 words)",
  "short_hook": "First 15 seconds hook for YouTube Short",
  "style": "Suno style for background music (e.g. 'gentle lullaby, soft piano, dreamy')",
  "mood": "One-word mood"
}}
""",
}


def _build_prompt(content_plan: dict) -> str:
    content_type = content_plan["type"]
    topic = content_plan["topic"]
    theme = content_plan.get("theme")
    theme_note = f"Seasonal theme: {theme} — weave this theme into the content." if theme else ""

    template = PROMPTS.get(content_type, PROMPTS["learning"])
    return template.format(base=_BASE_INSTRUCTIONS, topic=topic, theme_note=theme_note)


def write_content(content_plan: dict) -> dict:
    """Call Claude to generate all written content for today's video."""
    api_key = (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY") or "").strip()
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(content_plan)

    logger.debug("Sending prompt to Claude (model=%s)", MODEL)

    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Claude returned invalid JSON: %s", raw[:500])
        raise ValueError(f"Claude response was not valid JSON: {exc}") from exc

    _validate_written_content(result)
    logger.info("Claude wrote content: title=%s", result.get("title"))
    return result


def _validate_written_content(data: dict) -> None:
    required = {"title", "description", "tags", "lyrics", "script", "short_hook", "style", "mood"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Claude response missing required keys: {missing}")
    if not isinstance(data["tags"], list):
        raise ValueError("'tags' must be a list")
