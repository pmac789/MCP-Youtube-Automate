"""
main.py — Happy Melody Kids YouTube Automation Pipeline
Runs daily at 09:00 UTC via the schedule library.

Startup behaviour:
  - FORCE_RUN=true  → run pipeline once on startup, then schedule normally.
                       If it fails, log the error and wait for next 09:00 UTC run.
  - SKIP_STARTUP_RUN=true (or FORCE_RUN not set) → go straight to scheduler.

Failure behaviour:
  - Any step failure is caught, logged with the step name and reason, and the
    process stays alive waiting for the next scheduled run. No automatic retry.
"""

import os
import schedule
import time
import logging
from datetime import datetime, timezone

from content_calendar import get_todays_content
from claude_writer import write_content
from elevenlabs_music import generate_music
from heygen_video import generate_video
from youtube_uploader import upload_videos
from utils import setup_logging, cleanup_output


def run_pipeline() -> None:
    """Execute the full daily content pipeline. Raises on any step failure."""
    logger = logging.getLogger(__name__)
    logger.info("=== Pipeline started: %s ===", datetime.now(timezone.utc).isoformat())

    # Step 1 — pick today's content type and topic
    logger.info("[1/6] Selecting today's content...")
    try:
        content_plan = get_todays_content()
    except Exception as exc:
        raise RuntimeError(f"[1/6] Content calendar failed: {exc}") from exc
    logger.info("Content plan: type=%s, topic=%s", content_plan["type"], content_plan["topic"])

    # Step 2 — Claude writes lyrics, script, metadata
    logger.info("[2/6] Writing content with Claude...")
    try:
        written = write_content(content_plan)
    except Exception as exc:
        raise RuntimeError(f"[2/6] Claude content writing failed: {exc}") from exc
    logger.info("Title: %s", written["title"])

    # Step 3 — ElevenLabs generates voice audio
    logger.info("[3/6] Generating voice audio with ElevenLabs...")
    try:
        audio_path = generate_music(
            lyrics=written["lyrics"],
            style=written.get("style", "children's pop"),
            mood=written.get("mood", "happy"),
        )
    except Exception as exc:
        raise RuntimeError(f"[3/6] ElevenLabs TTS failed: {exc}") from exc
    logger.info("Audio saved: %s", audio_path)

    # Step 4 — HeyGen renders avatar lip-sync video + Short
    logger.info("[4/6] Rendering video with HeyGen...")
    try:
        video_paths = generate_video(
            script=written["script"],
            audio_path=audio_path,
            title=written["title"],
            content_type=content_plan["type"],
        )
    except Exception as exc:
        raise RuntimeError(f"[4/6] HeyGen video rendering failed: {exc}") from exc
    logger.info("Videos: main=%s, short=%s", video_paths["main"], video_paths["short"])

    # Step 5 — Upload to YouTube
    logger.info("[5/6] Uploading to YouTube...")
    try:
        upload_result = upload_videos(
            main_video_path=video_paths["main"],
            short_video_path=video_paths["short"],
            title=written["title"],
            description=written["description"],
            tags=written["tags"],
            short_hook=written["short_hook"],
        )
    except Exception as exc:
        raise RuntimeError(f"[5/6] YouTube upload failed: {exc}") from exc
    logger.info(
        "Uploaded: main=%s, short=%s",
        upload_result["main_id"],
        upload_result["short_id"],
    )

    # Step 6 — Cleanup temp files
    logger.info("[6/6] Cleaning up output folder...")
    cleanup_output()

    logger.info("=== Pipeline complete ===")


def _run_once(reason: str) -> None:
    """Run the pipeline once, log any failure, then return — never re-raise."""
    logger = logging.getLogger(__name__)
    logger.info("Running pipeline (%s)...", reason)
    try:
        run_pipeline()
    except RuntimeError as exc:
        # Step-level error — already has clear context from run_pipeline()
        logger.error("Pipeline failed: %s", exc)
        logger.error("Next attempt: 09:00 UTC tomorrow.")
    except Exception as exc:
        # Unexpected error
        logger.error("Pipeline failed with unexpected error: %s: %s", type(exc).__name__, exc)
        logger.error("Next attempt: 09:00 UTC tomorrow.")


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    force_run = os.environ.get("FORCE_RUN", "").lower() == "true"

    if force_run:
        _run_once("FORCE_RUN=true")

    logger.info("Scheduler active — daily run at 09:00 UTC")
    schedule.every().day.at("09:00").do(_run_once, reason="scheduled daily run")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
