"""
elevenlabs_music.py — Generates spoken audio via ElevenLabs Text-to-Speech API.

generate_music():
  Converts lyrics to speech using ElevenLabs TTS.
  POST /v1/text-to-speech/{voice_id} → streams MP3 to output/

generate_voiceover():
  Same as generate_music() but accepts a full script instead of lyrics.
  Strips [VISUAL: ...] markers before sending.

Voice selection:
  Set ELEVENLABS_VOICE_ID in the environment to override the default.
  Default fallback: Charlotte (XB0fDUnXU5powFXDhCwa) — bright, friendly tone.
  Find alternatives at elevenlabs.io/app/voice-library (search "child" or "kids").
"""

import os
import re
import uuid
import logging
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
OUTPUT_DIR = Path(__file__).parent / "output"

# Default voice used when ELEVENLABS_VOICE_ID env var is not set.
# Charlotte — bright, friendly tone that works well for kids content.
# Override by setting ELEVENLABS_VOICE_ID in Railway / .env.
DEFAULT_VOICE_ID = "XB0fDUnXU5powFXDhCwa"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_music(lyrics: str, style: str = "children's pop", mood: str = "happy") -> str:
    """
    Convert song lyrics to speech audio via ElevenLabs TTS.
    The resulting MP3 is used by HeyGen to lip-sync the avatar.

    Args:
        lyrics: Song lyrics (spoken aloud by the avatar).
        style:  Unused — kept for call-site compatibility.
        mood:   Unused — kept for call-site compatibility.

    Returns:
        Local file path string of the downloaded MP3.
    """
    api_key = _require_env("ELEVENLABS_API_KEY")
    voice_id = _require_env("ELEVENLABS_VOICE_ID", default=DEFAULT_VOICE_ID)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stem = str(uuid.uuid4())
    local_path = OUTPUT_DIR / f"music_{stem}.mp3"

    logger.info("Generating TTS audio via ElevenLabs...")
    _stream_tts(api_key, voice_id, lyrics, local_path)
    logger.info("Audio saved: %s", local_path)
    return str(local_path)


def generate_voiceover(script: str, output_filename: str | None = None) -> str:
    """
    Convert a full narration script to speech using ElevenLabs TTS.
    Strips [VISUAL: ...] markers automatically.

    Returns:
        Local file path string of the downloaded MP3.
    """
    api_key = _require_env("ELEVENLABS_API_KEY")
    voice_id = _require_env("ELEVENLABS_VOICE_ID", default=DEFAULT_VOICE_ID)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    clean_script = re.sub(r"\[VISUAL:[^\]]*\]", "", script).strip()
    stem = output_filename or str(uuid.uuid4())
    local_path = OUTPUT_DIR / f"{stem}_voiceover.mp3"

    _stream_tts(api_key, voice_id, clean_script, local_path)
    logger.info("Voiceover saved: %s", local_path)
    return str(local_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_env(name: str, default: str | None = None) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        if default is not None:
            logger.warning("%s not set — using default: %s", name, default)
            return default
        raise EnvironmentError(f"{name} is not set")
    return value


def _stream_tts(api_key: str, voice_id: str, text: str, local_path: Path) -> None:
    """Stream ElevenLabs TTS audio directly to a local file."""
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    with httpx.Client(timeout=120) as client:
        with client.stream(
            "POST",
            f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
