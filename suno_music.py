"""
suno_music.py — Sends lyrics to Suno AI API, polls until done, downloads MP3.

Suno API (unofficial / community endpoint) reference:
  POST /generate   → returns job id
  GET  /feed/{id}  → poll for status and audio_url
"""

import os
import time
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SUNO_BASE_URL = "https://studio-api.suno.ai"
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 60  # 10 minutes max
OUTPUT_DIR = Path(__file__).parent / "output"


def generate_music(lyrics: str, style: str = "children's pop", mood: str = "happy") -> str:
    """
    Submit lyrics to Suno, poll until the track is ready, download the MP3.
    Returns the local file path of the downloaded MP3.
    """
    api_key = os.environ.get("SUNO_API_KEY")
    if not api_key:
        raise EnvironmentError("SUNO_API_KEY is not set")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    job_id = _submit_job(api_key, lyrics, style, mood)
    logger.info("Suno job submitted: %s", job_id)

    audio_url = _poll_for_completion(api_key, job_id)
    logger.info("Suno audio ready: %s", audio_url)

    local_path = _download_audio(audio_url, job_id)
    logger.info("Audio downloaded: %s", local_path)
    return local_path


def _submit_job(api_key: str, lyrics: str, style: str, mood: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "prompt": lyrics,
        "tags": f"{style}, {mood}",
        "title": "Happy Melody Kids",
        "make_instrumental": False,
        "wait_audio": False,
    }

    response = requests.post(
        f"{SUNO_BASE_URL}/api/generate/v2/",
        json=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    # Suno returns a list of clips; take the first
    clips = data if isinstance(data, list) else data.get("clips", [])
    if not clips:
        raise RuntimeError(f"Suno returned no clips: {data}")
    return clips[0]["id"]


def _poll_for_completion(api_key: str, job_id: str) -> str:
    """Poll Suno until audio_url is available. Returns the audio URL."""
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        response = requests.get(
            f"{SUNO_BASE_URL}/api/feed/",
            params={"ids": job_id},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        clips = data if isinstance(data, list) else []
        if clips and clips[0].get("status") == "complete":
            audio_url = clips[0].get("audio_url")
            if audio_url:
                return audio_url

        status = clips[0].get("status", "unknown") if clips else "unknown"
        logger.debug("Suno poll attempt %d/%d — status: %s", attempt, MAX_POLL_ATTEMPTS, status)

        if status == "error":
            raise RuntimeError(f"Suno job {job_id} failed: {clips[0]}")

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"Suno job {job_id} did not complete within {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s")


def _download_audio(audio_url: str, job_id: str) -> str:
    """Download the MP3 from audio_url. Returns the local file path string."""
    local_path = OUTPUT_DIR / f"{job_id}.mp3"

    response = requests.get(audio_url, timeout=60, stream=True)
    response.raise_for_status()

    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(local_path)
