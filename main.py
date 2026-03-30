"""
main.py — Happy Melody Kids YouTube Automation Pipeline
Runs daily at 09:00 UTC via the schedule library.

Startup behaviour:
  - Always runs the pipeline once immediately on startup (smoke test).
  - FORCE_RUN=true  → same behaviour, useful to re-trigger via Railway without
                       waiting for the scheduler (just redeploy with the var set).
  - Set SKIP_STARTUP_RUN=true to disable the immediate run (schedule-only mode).
"""

import os
import schedule
import time
import logging
from datetime import datetime

from content_calendar import get_todays_content
from claude_writer import write_content
from elevenlabs_music import generate_music
from heygen_video import generate_video
from youtube_uploader import upload_videos
from utils import setup_logging, cleanup_output


def run_pipeline() -> None:
    """Execute the full daily content pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("=== Pipeline started: %s ===", datetime.utcnow().isoformat())

    # Step 1 — pick today's content type and topic
    logger.info("[1/6] Selecting today's content...")
    content_plan = get_todays_content()
    logger.info("Content plan: type=%s, topic=%s", content_plan["type"], content_plan["topic"])

    # Step 2 — Claude writes lyrics, script, metadata
    logger.info("[2/6] Writing content with Claude...")
    written = write_content(content_plan)
    logger.info("Title: %s", written["title"])

    # Step 3 — ElevenLabs generates music + voice
    logger.info("[3/6] Generating music + voice with ElevenLabs...")
    audio_path = generate_music(
        lyrics=written["lyrics"],
        style=written.get("style", "children's pop"),
        mood=written.get("mood", "happy"),
    )
    logger.info("Audio saved: %s", audio_path)

    # Step 4 — HeyGen renders avatar lip-sync video + Short
    logger.info("[4/6] Rendering video with HeyGen...")
    video_paths = generate_video(
        script=written["script"],
        audio_path=audio_path,
        title=written["title"],
        content_type=content_plan["type"],
    )
    logger.info("Videos: main=%s, short=%s", video_paths["main"], video_paths["short"])

    # Step 5 — Upload to YouTube
    logger.info("[5/6] Uploading to YouTube...")
    upload_result = upload_videos(
        main_video_path=video_paths["main"],
        short_video_path=video_paths["short"],
        title=written["title"],
        description=written["description"],
        tags=written["tags"],
        short_hook=written["short_hook"],
    )
    logger.info(
        "Uploaded: main=%s, short=%s",
        upload_result["main_id"],
        upload_result["short_id"],
    )

    # Step 6 — Cleanup temp files
    logger.info("[6/6] Cleaning up output folder...")
    cleanup_output()

    logger.info("=== Pipeline complete ===")


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    force_run = os.environ.get("FORCE_RUN", "").lower() == "true"
    skip_startup = os.environ.get("SKIP_STARTUP_RUN", "").lower() == "true"

    # Run immediately on startup unless explicitly skipped
    if force_run or not skip_startup:
        reason = "FORCE_RUN=true" if force_run else "startup test run"
        logger.info("Running pipeline immediately (%s)...", reason)
        run_pipeline()

    logger.info("Scheduler active — daily run at 09:00 UTC")
    schedule.every().day.at("09:00").do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
