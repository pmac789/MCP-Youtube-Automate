# Changelog

All notable changes to this project are documented here.
Format: date, short title, bullet-point description.

---

## 2026-03-30 — Replace HeyGen with local FFmpeg video builder

- Added `video_builder.py`: renders animated 1280×720 main video and 720×1280 Short using FFmpeg filtergraph — no external video API needed
- Deleted `heygen_video.py` entirely
- FFmpeg filtergraph: animated gradient background (geq), drawtext title, bouncing ♪♫ notes, timed lyrics, watermark
- `main.py`: updated import to `video_builder`, updated step 4 log message and error message
- `.env.example`: removed `HEYGEN_API_KEY` and `HEYGEN_AVATAR_ID`, added FFmpeg comment
- `railway.toml`: added `nixPackages = ["ffmpeg"]` so Railway installs FFmpeg at build time
- Cost saving: eliminates $29/mo HeyGen subscription

---

## 2026-03-29 — HeyGen debugging and stabilisation

- Added detailed JSON logging of every HeyGen API request and response to diagnose avatar/job failures
- Triggered Railway redeploy (empty commit) to pick up fixes

### HeyGen integration fixes (multiple commits)
- Fixed HeyGen avatar: photo avatar `823e02e85726482c80bfff9d6baceb4d` not trained for API use — added built-in fallback `Abigail_expressive_2024112501`
- Fixed HeyGen response parsing: API returns `code=100` for success (not HTTP status); extract `data['id']` not `data['asset_id']`
- Fixed HeyGen upload URL: asset upload must use `upload.heygen.com/v1/asset` subdomain, not `api.heygen.com`
- Fixed HeyGen audio upload: must send raw binary body with `Content-Type: audio/mpeg`, not multipart form

### Pipeline reliability fixes
- Fixed crash loop: `FORCE_RUN=true` + unhandled exception caused Railway to restart instantly, burning Claude credits. Wrapped all startup pipeline runs in try/except — failures now log and wait for next 09:00 UTC run
- Fixed ElevenLabs 404: `/v1/music/generations` does not exist on public API — replaced with TTS endpoint `/v1/text-to-speech/{voice_id}` which is what HeyGen lip-sync needs
- Fixed all env var trailing newline errors: added `.strip()` to every `os.environ.get()` call across `claude_writer.py`, `elevenlabs_music.py`, `heygen_video.py`, `youtube_uploader.py`

### Infrastructure
- Added `FORCE_RUN=true` env var support: run pipeline once on startup then schedule normally
- Excluded all `*.json` files from git to prevent OAuth credential leaks
- Automated `token.pickle` for Railway: base64-encode locally, store as `YOUTUBE_TOKEN_B64` env var, decoded automatically at startup

---

## 2026-03-29 — Initial build and stack setup

- Created full project structure: `main.py`, `content_calendar.py`, `claude_writer.py`, `elevenlabs_music.py`, `heygen_video.py`, `youtube_uploader.py`, `auth_setup.py`, `utils.py`
- Weekly content schedule: Mon/Wed learning, Tue/Fri song, Thu/Sun movement, Sat story, daily Short
- Seasonal topic overrides: Christmas, Halloween, Valentine's Day, Easter, Back to School
- Claude (`claude-opus-4-5`) writes lyrics, script with `[VISUAL: ...]` markers, title, description, tags
- ElevenLabs TTS (`eleven_multilingual_v2`) generates voice audio
- HeyGen v2 API for avatar lip-sync video (1920×1080 main + 1080×1920 Short)
- YouTube Data API v3 upload with `madeForKids=True`, resumable chunked upload
- Railway deployment via nixpacks, `startCommand = "python main.py"`
- Replaced original Pictory video renderer with HeyGen for better animated character quality
- All secrets loaded from environment variables, never hardcoded
