#!/usr/bin/env bash
# render-colors.sh — Renders the Learn Colors video using Remotion.
#
# Usage:
#   cd remotion
#   ./render-colors.sh [path-to-audio.mp3]
#
# If no audio path is given, defaults to ../output/audio.mp3
# The rendered video is saved to ../output/learn_colors.mp4
#
# Prerequisites:
#   npm install   (run once in the remotion/ folder)

set -e

AUDIO="${1:-../output/audio.mp3}"
OUTPUT="../output/learn_colors.mp4"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Happy Melody Kids — Learn Colors Renderer ==="

# Install deps if needed
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
  echo "[1/3] Installing npm dependencies..."
  (cd "$SCRIPT_DIR" && npm install --silent)
else
  echo "[1/3] npm dependencies already installed."
fi

# Copy audio into public/ so staticFile('audio.mp3') can find it
if [ -f "$AUDIO" ]; then
  echo "[2/3] Copying audio: $AUDIO → public/audio.mp3"
  cp "$AUDIO" "$SCRIPT_DIR/public/audio.mp3"
else
  echo "[2/3] WARNING: Audio file not found at $AUDIO — video will have no sound."
fi

# Ensure output directory exists
mkdir -p "$(dirname "$SCRIPT_DIR/$OUTPUT")"

# Render
echo "[3/3] Rendering LearnColors composition → $OUTPUT"
(cd "$SCRIPT_DIR" && npx remotion render src/index.tsx LearnColors "$OUTPUT" --concurrency=1)

echo ""
echo "Done! Video saved to: $OUTPUT"
