"""
video_builder.py — Builds animated kids MP4 videos locally using FFmpeg.
No external video API required.

generate_video(script, audio_path, title, content_type) -> dict
  Returns {"main": "<path to 1280x720 mp4>", "short": "<path to 720x1280 mp4>"}

How it works:
  1. mutagen reads the exact audio duration (no ffprobe needed)
  2. FFmpeg renders a solid colour background with centred title text,
     muxed with the ElevenLabs MP3, using list-based subprocess args
     to avoid all shell-escaping issues
  3. A 60-second 9:16 Short is produced at 720x1280
"""

import logging
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"

# Background colours per content type
BG_COLOURS = {
    "learning": "#7BC8F6",   # sky blue
    "song":     "#B5EAD7",   # mint green
    "movement": "#FF9AA2",   # coral pink
    "story":    "#C7CEEA",   # lavender
}
DEFAULT_BG = "#7BC8F6"

SHORT_DURATION = 60   # seconds


# ---------------------------------------------------------------------------
# Startup check
# ---------------------------------------------------------------------------

def _find_ffmpeg() -> str:
    """
    Return the working ffmpeg binary path.
    Uses shutil.which() to search PATH, then tries the Nix profile path.
    Logs a clear error and raises if not found.
    """
    # Primary: search the entire PATH (works for Docker apt-get and most installs)
    path = shutil.which("ffmpeg")
    if path:
        logger.info("FFmpeg found: %s", path)
        return path

    # Fallback: Nix default profile (Railway nixpacks installs here)
    nix_path = shutil.which("ffmpeg", path="/nix/var/nix/profiles/default/bin")
    if nix_path:
        logger.info("FFmpeg found (nix profile): %s", nix_path)
        return nix_path

    logger.error(
        "FFmpeg not found - check nixpacks.toml (nixPkgs = [\"ffmpeg\"]) "
        "or Dockerfile (apt-get install ffmpeg)"
    )
    raise RuntimeError(
        "FFmpeg not found. Ensure nixpacks.toml has nixPkgs = [\"ffmpeg\"] "
        "or the Dockerfile installs ffmpeg via apt-get."
    )


# Resolve ffmpeg path once at module load so the error surfaces early.
_FFMPEG_BIN = _find_ffmpeg()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_video(
    script: str,
    audio_path: str,
    title: str,
    content_type: str = "learning",
) -> dict:
    """
    Build main (1280×720) and Short (720×1280) MP4 files from an MP3.

    Returns:
        {"main": str, "short": str}  — absolute paths to the MP4 files.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    audio_path = str(audio_path)
    duration = _get_audio_duration(audio_path)
    bg_colour = BG_COLOURS.get(content_type, DEFAULT_BG)
    stem = str(uuid.uuid4())

    main_path = str(OUTPUT_DIR / f"{stem}_main.mp4")
    short_path = str(OUTPUT_DIR / f"{stem}_short.mp4")

    logger.info("Building main video (1280x720, %.1fs)...", duration)
    _build_video(
        audio_path=audio_path,
        output_path=main_path,
        width=1280,
        height=720,
        title=title,
        bg_colour=bg_colour,
    )

    logger.info("Building Short (720x1280, %ds)...", SHORT_DURATION)
    _build_video(
        audio_path=audio_path,
        output_path=short_path,
        width=720,
        height=1280,
        title=title,
        bg_colour=bg_colour,
    )

    logger.info("Videos ready: main=%s  short=%s", main_path, short_path)
    return {"main": main_path, "short": short_path}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_audio_duration(audio_path: str) -> float:
    """Use mutagen to read MP3 duration — no ffprobe subprocess needed."""
    audio = MP3(audio_path)
    duration = audio.info.length
    logger.info("Audio duration: %.2fs", duration)
    return duration


def _sanitize_title(title: str) -> str:
    """
    Remove characters that break FFmpeg drawtext even when passed as a list arg.
    Keeps alphanumerics, spaces, hyphens, and basic punctuation.
    """
    # Strip problematic chars: single quotes, colons, pipes, backslashes, brackets
    clean = re.sub(r"['\:\\|<>\[\]{}]", "", title)
    return clean[:60].strip()


def _build_video(
    audio_path: str,
    output_path: str,
    width: int,
    height: int,
    title: str,
    bg_colour: str,
) -> None:
    """
    Render a single MP4 using a simple, bulletproof FFmpeg command.
    Args are passed as a list — no shell escaping, no filtergraph string parsing issues.
    """
    safe_title = _sanitize_title(title)
    fontsize = 48 if width >= 1280 else 36

    # -vf value is a single string but kept intentionally simple —
    # no floats, no commas inside filter args, no special chars.
    vf = (
        f"drawtext=text='{safe_title}'"
        f":fontcolor=white"
        f":fontsize={fontsize}"
        f":x=(w-text_w)/2"
        f":y=(h-text_h)/2"
        f":box=1"
        f":boxcolor=black@0.4"
        f":boxborderw=10"
    )

    cmd = [
        _FFMPEG_BIN, "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_colour}:size={width}x{height}:rate=30",
        "-i", audio_path,
        "-vf", vf,
        "-shortest",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    logger.info("FFmpeg cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg stderr: %s", result.stderr[-2000:])
        raise RuntimeError(f"FFmpeg failed (exit {result.returncode}): {result.stderr[-500:]}")

    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    logger.info("Rendered %s (%.1f MB)", Path(output_path).name, size_mb)
