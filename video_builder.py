"""
video_builder.py — Builds animated kids MP4 videos locally using FFmpeg.
No external video API required.

generate_video(script, audio_path, title, content_type) -> dict
  Returns {"main": "<path to 1280x720 mp4>", "short": "<path to 720x1280 mp4>"}

How it works:
  1. ffprobe detects the exact audio duration
  2. FFmpeg renders an animated background + title + bouncing notes + lyrics
     all in one pass, muxed with the ElevenLabs MP3
  3. A 60-second 9:16 Short is cropped from the main video
"""

import json
import logging
import re
import subprocess
import uuid
from pathlib import Path

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
    lyrics_lines = _extract_lyrics_lines(script)
    stem = str(uuid.uuid4())

    main_path = str(OUTPUT_DIR / f"{stem}_main.mp4")
    short_path = str(OUTPUT_DIR / f"{stem}_short.mp4")

    logger.info("Building main video (1280×720, %.1fs)...", duration)
    _build_video(
        audio_path=audio_path,
        output_path=main_path,
        width=1280,
        height=720,
        duration=duration,
        title=title,
        lyrics_lines=lyrics_lines,
        bg_colour=bg_colour,
    )

    logger.info("Building Short (720×1280, %ds)...", SHORT_DURATION)
    _build_video(
        audio_path=audio_path,
        output_path=short_path,
        width=720,
        height=1280,
        duration=min(duration, SHORT_DURATION),
        title=title,
        lyrics_lines=lyrics_lines,
        bg_colour=bg_colour,
    )

    logger.info("Videos ready: main=%s  short=%s", main_path, short_path)
    return {"main": main_path, "short": short_path}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_audio_duration(audio_path: str) -> float:
    """Use ffprobe to get the duration of the audio file in seconds."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    duration = float(info["format"]["duration"])
    logger.info("Audio duration: %.2fs", duration)
    return duration


def _extract_lyrics_lines(script: str) -> list[str]:
    """
    Strip [VISUAL: ...] markers and blank lines, return up to 20 short lines.
    Each line will be shown sequentially during the video.
    """
    clean = re.sub(r"\[VISUAL:[^\]]*\]", "", script)
    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
    # Keep lines short enough to fit on screen
    trimmed = [ln[:60] for ln in lines]
    return trimmed[:20]


def _escape_ffmpeg_text(text: str) -> str:
    """Escape characters that FFmpeg drawtext treats as special."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace(",", "\\,")
    return text


def _build_lyrics_filter(lines: list[str], duration: float, width: int, height: int) -> str:
    """
    Build a chain of drawtext filters that shows each lyrics line
    for an equal share of the total duration.
    """
    if not lines:
        return ""

    secs_per_line = duration / len(lines)
    filters = []
    y_pos = int(height * 0.62)

    for i, line in enumerate(lines):
        start = i * secs_per_line
        end = start + secs_per_line
        safe = _escape_ffmpeg_text(line)
        filters.append(
            f"drawtext=text='{safe}'"
            f":fontsize={max(18, int(width / 32))}"
            f":fontcolor=white"
            f":x=(w-text_w)/2"
            f":y={y_pos}"
            f":shadowcolor=black@0.6:shadowx=2:shadowy=2"
            f":enable='between(t,{start:.2f},{end:.2f})'"
        )
    return ",".join(filters)


def _build_video(
    audio_path: str,
    output_path: str,
    width: int,
    height: int,
    duration: float,
    title: str,
    lyrics_lines: list[str],
    bg_colour: str,
) -> None:
    """Render a single MP4 using FFmpeg filtergraph."""
    # Convert hex colour to R,G,B for geq filter
    hex_c = bg_colour.lstrip("#")
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)

    # Animated gradient: base colour with a gentle sine-wave brightness pulse
    geq_filter = (
        f"geq=r='{r}+20*sin(2*PI*t/4)'"
        f":g='{g}+20*sin(2*PI*t/4)'"
        f":b='{b}+30*sin(2*PI*t/3)'"
    )

    title_safe = _escape_ffmpeg_text(title[:55])
    title_fontsize = max(24, int(width / 22))
    notes_fontsize = max(32, int(width / 14))
    watermark_fontsize = max(14, int(width / 52))

    # Bouncing musical notes — two notes out of phase with each other
    note1_y = f"h/2-{int(height*0.18)}+{int(height*0.08)}*sin(2*PI*t/1.8)"
    note2_y = f"h/2-{int(height*0.18)}+{int(height*0.08)}*sin(2*PI*t/1.8+PI)"
    note1_x = int(width * 0.15)
    note2_x = int(width * 0.78)

    lyrics_filter = _build_lyrics_filter(lyrics_lines, duration, width, height)

    # Build the full filtergraph
    vf_parts = [
        # Animated background
        geq_filter,
        # Title — top third, bold white with shadow
        f"drawtext=text='{title_safe}'"
        f":fontsize={title_fontsize}"
        f":fontcolor=white"
        f":x=(w-text_w)/2"
        f":y=h*0.12"
        f":shadowcolor=black@0.7:shadowx=3:shadowy=3",
        # Bouncing note 1
        f"drawtext=text='♪'"
        f":fontsize={notes_fontsize}"
        f":fontcolor=yellow@0.9"
        f":x={note1_x}"
        f":y={note1_y}"
        f":shadowcolor=black@0.5:shadowx=2:shadowy=2",
        # Bouncing note 2
        f"drawtext=text='♫'"
        f":fontsize={notes_fontsize}"
        f":fontcolor=yellow@0.9"
        f":x={note2_x}"
        f":y={note2_y}"
        f":shadowcolor=black@0.5:shadowx=2:shadowy=2",
        # Watermark
        f"drawtext=text='Happy Melody Kids'"
        f":fontsize={watermark_fontsize}"
        f":fontcolor=white@0.55"
        f":x=w-text_w-16"
        f":y=h-text_h-12",
    ]

    if lyrics_filter:
        vf_parts.append(lyrics_filter)

    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=s={width}x{height}:r=30",   # synthetic video source
        "-i", audio_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        output_path,
    ]

    logger.debug("FFmpeg cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg stderr: %s", result.stderr[-2000:])
        raise RuntimeError(f"FFmpeg failed (exit {result.returncode}): {result.stderr[-500:]}")

    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    logger.info("Rendered %s (%.1f MB)", Path(output_path).name, size_mb)
