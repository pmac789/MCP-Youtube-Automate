"""
elevenlabs_music.py — Generates kids music and voiceover via ElevenLabs API.

generate_music():
  POST /v1/music/generations with lyrics + style prompt
  Polls job status until complete
  Downloads finished MP3 to output/

generate_voiceover():
  POST /v1/text-to-speech/{voice_id}
  Streams response directly to MP3 file in output/
"""

import os
import time
import uuid
import logging
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 60   # 10 minutes max
OUTPUT_DIR = Path(__file__).parent / "output"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_music(lyrics: str, style: str = "children's pop", mood: str = "happy") -> str:
    """
    Submit lyrics to ElevenLabs Music Generation, poll until done, download MP3.

    Args:
        lyrics: Song lyrics to generate music for.
        style:  Musical style description (e.g. "upbeat children's pop, xylophone").
        mood:   Single-word mood (e.g. "happy", "playful").

    Returns:
        Local file path string of the downloaded MP3.
    """
    api_key = _require_env("ELEVENLABS_API_KEY")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prompt = f"{style}, {mood} mood. Lyrics:\n{lyrics}"

    generation_id = _submit_music_job(api_key, prompt)
    logger.info("ElevenLabs music job submitted: %s", generation_id)

    audio_url = _poll_music_completion(api_key, generation_id)
    logger.info("ElevenLabs music ready: %s", audio_url)

    local_path = _download_audio(audio_url, generation_id, prefix="music")
    logger.info("Music downloaded: %s", local_path)
    return local_path


def generate_voiceover(script: str, output_filename: str | None = None) -> str:
    """
    Convert script text to speech using ElevenLabs TTS.

    Args:
        script:          Narration text (VISUAL markers stripped automatically).
        output_filename: Optional filename stem (without extension).

    Returns:
        Local file path string of the downloaded MP3.
    """
    import re

    api_key = _require_env("ELEVENLABS_API_KEY")
    voice_id = _require_env("ELEVENLABS_VOICE_ID")
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

def _require_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise EnvironmentError(f"{name} is not set")
    return value


def _auth_headers(api_key: str) -> dict:
    return {"xi-api-key": api_key, "Content-Type": "application/json"}


def _submit_music_job(api_key: str, prompt: str) -> str:
    """POST to /v1/music/generations. Returns generation_id."""
    payload = {
        "prompt": prompt,
        "duration_seconds": 180,   # ~3 min for a full kids song
        "output_format": "mp3_44100_128",
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{ELEVENLABS_BASE_URL}/v1/music/generations",
            headers=_auth_headers(api_key),
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    generation_id = data.get("generation_id") or data.get("id")
    if not generation_id:
        raise RuntimeError(f"ElevenLabs music/generations returned no ID: {data}")
    return generation_id


def _poll_music_completion(api_key: str, generation_id: str) -> str:
    """Poll GET /v1/music/generations/{id} until status == 'complete'. Returns audio URL."""
    headers = {"xi-api-key": api_key}

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{ELEVENLABS_BASE_URL}/v1/music/generations/{generation_id}",
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        status = data.get("status", "").lower()

        if status == "complete":
            audio_url = data.get("audio_url") or data.get("url")
            if not audio_url:
                raise RuntimeError(f"ElevenLabs job complete but no audio_url: {data}")
            return audio_url

        if status in ("failed", "error"):
            raise RuntimeError(
                f"ElevenLabs music job {generation_id} failed: {data.get('error', data)}"
            )

        logger.debug(
            "ElevenLabs music poll %d/%d — status: %s",
            attempt, MAX_POLL_ATTEMPTS, status,
        )
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"ElevenLabs music job {generation_id} timed out after "
        f"{MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s"
    )


def _download_audio(audio_url: str, stem: str, prefix: str = "audio") -> str:
    """Stream-download audio from URL. Returns local file path string."""
    local_path = OUTPUT_DIR / f"{prefix}_{stem}.mp3"

    with httpx.Client(timeout=120, follow_redirects=True) as client:
        with client.stream("GET", audio_url) as response:
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)

    return str(local_path)


def _stream_tts(api_key: str, voice_id: str, text: str, local_path: Path) -> None:
    """Stream TTS audio directly to a local file."""
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.8,
            "style": 0.3,
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
