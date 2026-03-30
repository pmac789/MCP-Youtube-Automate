"""
heygen_video.py — Generates avatar lip-sync videos via HeyGen v2 API.

Flow:
  1. Upload ElevenLabs MP3 → /v1/asset                  → asset_id
  2. Submit main video job (1920×1080) → /v2/video/generate  → video_id
  3. Submit Short job (1080×1920)     → /v2/video/generate  → video_id
  4. Poll /v1/video_status.get until status == "completed"
  5. Download both MP4s to /output/

Avatar ID is read from HEYGEN_AVATAR_ID env var.
Background colours are chosen per content type.
"""

import os
import time
import logging
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

HEYGEN_BASE_URL = "https://api.heygen.com"
POLL_INTERVAL_SECONDS = 15
MAX_POLL_ATTEMPTS = 80   # 20 minutes max
OUTPUT_DIR = Path(__file__).parent / "output"

# ---------------------------------------------------------------------------
# Background colour presets per content type
# Avatar ID is read at runtime from HEYGEN_AVATAR_ID env var
# ---------------------------------------------------------------------------

BACKGROUND_BY_TYPE: dict[str, dict] = {
    "learning":  {"type": "color", "value": "#FFE066"},   # warm yellow
    "song":      {"type": "color", "value": "#B5EAD7"},   # soft green
    "movement":  {"type": "color", "value": "#FF9AA2"},   # energetic pink
    "story":     {"type": "color", "value": "#C7CEEA"},   # calm lavender
}

DEFAULT_BACKGROUND = BACKGROUND_BY_TYPE["learning"]


def _get_avatar_id() -> str:
    avatar_id = (os.environ.get("HEYGEN_AVATAR_ID") or "").strip()
    if not avatar_id:
        raise EnvironmentError("HEYGEN_AVATAR_ID is not set")
    return avatar_id


def generate_video(script: str, audio_path: str, title: str, content_type: str = "learning") -> dict:
    """
    Generate a lip-synced avatar video (main + Short) via HeyGen.

    Args:
        script:       Full narration script (used as subtitle / teleprompter text).
        audio_path:   Local path to the Suno-generated MP3.
        title:        Video title (used in HeyGen job metadata).
        content_type: One of 'learning', 'song', 'movement', 'story'.

    Returns:
        dict with keys "main" (str path) and "short" (str path).
    """
    api_key = (os.environ.get("HEYGEN_API_KEY") or "").strip()
    if not api_key:
        raise EnvironmentError("HEYGEN_API_KEY is not set")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    avatar_id = _get_avatar_id()
    background = BACKGROUND_BY_TYPE.get(content_type, DEFAULT_BACKGROUND)

    # Step 1 — upload audio
    asset_id = _upload_audio(api_key, audio_path)
    logger.info("HeyGen audio asset uploaded: %s", asset_id)

    # Step 2 — submit main video (16:9)
    main_video_id = _submit_video_job(
        api_key=api_key,
        asset_id=asset_id,
        script=script,
        title=f"{title} (main)",
        width=1920,
        height=1080,
        avatar_id=avatar_id,
        background=background,
    )
    logger.info("HeyGen main job submitted: %s", main_video_id)

    # Step 3 — submit Short (9:16)
    short_video_id = _submit_video_job(
        api_key=api_key,
        asset_id=asset_id,
        script=script,
        title=f"{title} (short)",
        width=1080,
        height=1920,
        avatar_id=avatar_id,
        background=background,
    )
    logger.info("HeyGen Short job submitted: %s", short_video_id)

    # Step 4 — poll both to completion
    main_url = _poll_for_completion(api_key, main_video_id, label="main")
    short_url = _poll_for_completion(api_key, short_video_id, label="short")

    # Step 5 — download
    main_path = _download_video(main_url, main_video_id, suffix="main")
    short_path = _download_video(short_url, short_video_id, suffix="short")

    logger.info("HeyGen videos ready: main=%s  short=%s", main_path, short_path)
    return {"main": main_path, "short": short_path}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key, "Content-Type": "application/json"}


def _upload_audio(api_key: str, audio_path: str) -> str:
    """Upload MP3 to HeyGen asset store. Returns asset_id."""
    file_path = Path(audio_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    upload_headers = {
        "X-Api-Key": api_key,
        "Content-Type": "audio/mpeg",
    }

    with httpx.Client(timeout=120) as client:
        with open(file_path, "rb") as f:
            response = client.post(
                f"{HEYGEN_BASE_URL}/v1/asset",
                headers=upload_headers,
                content=f.read(),
            )
        response.raise_for_status()

    data = response.json()
    asset_id = data.get("data", {}).get("asset_id") or data.get("asset_id")
    if not asset_id:
        raise RuntimeError(f"HeyGen asset upload failed: {data}")
    return asset_id


def _submit_video_job(
    api_key: str,
    asset_id: str,
    script: str,
    title: str,
    width: int,
    height: int,
    avatar_id: str,
    background: dict,
) -> str:
    """Submit a /v2/video/generate job. Returns video_id."""
    import re
    clean_script = re.sub(r"\[VISUAL:[^\]]*\]", "", script).strip()

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "audio",
                    "audio_asset_id": asset_id,
                },
                "background": background,
            }
        ],
        "dimension": {"width": width, "height": height},
        "aspect_ratio": None,
        "test": False,
        "caption": False,
        "title": title[:80],
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{HEYGEN_BASE_URL}/v2/video/generate",
            headers=_headers(api_key),
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    video_id = data.get("data", {}).get("video_id") or data.get("video_id")
    if not video_id:
        raise RuntimeError(f"HeyGen video/generate failed: {data}")
    return video_id


def _poll_for_completion(api_key: str, video_id: str, label: str = "") -> str:
    """Poll /v1/video_status.get until status == 'completed'. Returns video_url."""
    tag = f"[{label}] " if label else ""

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{HEYGEN_BASE_URL}/v1/video_status.get",
                headers=_headers(api_key),
                params={"video_id": video_id},
            )
            response.raise_for_status()

        data = response.json()
        job = data.get("data", {})
        status = job.get("status", "").lower()

        if status == "completed":
            video_url = job.get("video_url")
            if not video_url:
                raise RuntimeError(f"HeyGen {tag}job complete but no video_url: {job}")
            return video_url

        if status in ("failed", "error"):
            raise RuntimeError(f"HeyGen {tag}job {video_id} failed: {job.get('error', job)}")

        logger.debug(
            "HeyGen %spoll %d/%d — status: %s  progress: %s%%",
            tag, attempt, MAX_POLL_ATTEMPTS, status, job.get("progress", "?"),
        )
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"HeyGen {tag}job {video_id} timed out after "
        f"{MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s"
    )


def _download_video(video_url: str, video_id: str, suffix: str = "main") -> str:
    """Stream-download MP4 from HeyGen CDN. Returns local file path string."""
    local_path = OUTPUT_DIR / f"{video_id}_{suffix}.mp4"

    with httpx.Client(timeout=300, follow_redirects=True) as client:
        with client.stream("GET", video_url) as response:
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=65536):
                    f.write(chunk)

    return str(local_path)
