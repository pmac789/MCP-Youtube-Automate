"""
pictory_video.py — Sends script + audio to Pictory AI, polls until done,
downloads the rendered MP4 for both the main video and the YouTube Short.

Pictory REST API v1 reference:
  POST /video/storyboard  → create job
  GET  /jobs/{id}         → poll status
  GET  /video/{id}/url    → get download URL
"""

import os
import time
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PICTORY_BASE_URL = "https://api.pictory.ai/pictoryapis/v1"
POLL_INTERVAL_SECONDS = 15
MAX_POLL_ATTEMPTS = 80  # ~20 minutes max
OUTPUT_DIR = Path(__file__).parent / "output"

# Short clip: first N seconds to extract for the YouTube Short
SHORT_DURATION_SECONDS = 60


def generate_video(script: str, audio_path: str, title: str) -> dict:
    """
    Send script + audio to Pictory, wait for render, download both videos.
    Returns dict: { "main": "<path>", "short": "<path>" }
    """
    api_key = os.environ.get("PICTORY_API_KEY")
    client_id = os.environ.get("PICTORY_CLIENT_ID")
    if not api_key or not client_id:
        raise EnvironmentError("PICTORY_API_KEY and PICTORY_CLIENT_ID must be set")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    auth_token = _get_auth_token(api_key, client_id)

    job_id = _submit_storyboard(auth_token, script, audio_path, title)
    logger.info("Pictory job submitted: %s", job_id)

    main_url = _poll_for_completion(auth_token, job_id)
    logger.info("Pictory render complete: %s", main_url)

    main_path = _download_video(main_url, job_id, suffix="main")

    short_job_id = _submit_short(auth_token, job_id)
    short_url = _poll_for_completion(auth_token, short_job_id)
    short_path = _download_video(short_url, short_job_id, suffix="short")

    return {"main": main_path, "short": short_path}


def _get_auth_token(api_key: str, client_id: str) -> str:
    response = requests.post(
        f"{PICTORY_BASE_URL}/user/login",
        json={"apiKey": api_key, "clientId": client_id},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("data", {}).get("token")
    if not token:
        raise RuntimeError(f"Pictory login failed: {data}")
    return token


def _submit_storyboard(auth_token: str, script: str, audio_path: str, title: str) -> str:
    """Submit a video creation job. Returns job ID."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Parse script into scenes split by [VISUAL: ...] markers
    scenes = _parse_script_to_scenes(script)

    payload = {
        "videoName": title,
        "videoDescription": title,
        "language": "en",
        "videoWidth": 1920,
        "videoHeight": 1080,
        "scenes": scenes,
        "audio": {
            "aiVoiceOver": {"speaker": "aria", "speed": "100", "amplifyLevel": "1"},
            "autoBackgroundMusic": False,
        },
    }

    response = requests.post(
        f"{PICTORY_BASE_URL}/video/storyboard",
        json=payload,
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    job_id = data.get("data", {}).get("jobId")
    if not job_id:
        raise RuntimeError(f"Pictory storyboard submission failed: {data}")
    return job_id


def _submit_short(auth_token: str, source_job_id: str) -> str:
    """Request a vertical Short (9:16) clip from the first portion of the main video."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    payload = {
        "sourceJobId": source_job_id,
        "videoWidth": 1080,
        "videoHeight": 1920,
        "startTime": 0,
        "endTime": SHORT_DURATION_SECONDS,
    }
    response = requests.post(
        f"{PICTORY_BASE_URL}/video/short",
        json=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    job_id = data.get("data", {}).get("jobId")
    if not job_id:
        raise RuntimeError(f"Pictory short submission failed: {data}")
    return job_id


def _poll_for_completion(auth_token: str, job_id: str) -> str:
    """Poll Pictory until the job is complete. Returns the video download URL."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        response = requests.get(
            f"{PICTORY_BASE_URL}/jobs/{job_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        job_data = data.get("data", {})
        status = job_data.get("status", "").lower()

        if status == "complete":
            video_url = job_data.get("videoUrl") or job_data.get("renderUrl")
            if video_url:
                return video_url
            raise RuntimeError(f"Pictory job complete but no videoUrl: {job_data}")

        if status in ("error", "failed"):
            raise RuntimeError(f"Pictory job {job_id} failed: {job_data}")

        logger.debug("Pictory poll %d/%d — status: %s", attempt, MAX_POLL_ATTEMPTS, status)
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"Pictory job {job_id} timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s")


def _download_video(video_url: str, job_id: str, suffix: str = "main") -> str:
    local_path = OUTPUT_DIR / f"{job_id}_{suffix}.mp4"

    response = requests.get(video_url, timeout=120, stream=True)
    response.raise_for_status()

    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=65536):
            f.write(chunk)

    return str(local_path)


def _parse_script_to_scenes(script: str) -> list[dict]:
    """Split the script on [VISUAL: ...] markers into Pictory scene objects."""
    import re

    parts = re.split(r"\[VISUAL:[^\]]*\]", script)
    visuals = re.findall(r"\[VISUAL:([^\]]*)\]", script)

    scenes = []
    for i, text in enumerate(parts):
        text = text.strip()
        if not text:
            continue
        scene: dict = {"text": text, "splitTextOnNewLine": True, "splitTextOnPeriod": False}
        if i < len(visuals):
            scene["searchQuery"] = visuals[i].strip()
        scenes.append(scene)

    return scenes if scenes else [{"text": script, "splitTextOnNewLine": True}]
