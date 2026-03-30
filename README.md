# MCP-Youtube-Automate — Happy Melody Kids

Fully automated YouTube content pipeline for the **Happy Melody Kids** channel (ages 1–6).
Runs daily at 09:00 UTC, generating a full-length video **and** a YouTube Short from scratch using AI.

---

## Stack & cost

| Service       | Purpose                          | Cost     |
|---------------|----------------------------------|----------|
| Claude API    | Writes scripts + lyrics          | ~$8/mo   |
| ElevenLabs    | Voice narration (TTS)            | $11/mo   |
| FFmpeg        | Animated video rendering (local) | Free     |
| Railway       | Hosts the bot 24/7               | $5/mo    |
| **Total**     |                                  | **~$24/mo** |

---

## Pipeline overview

```
content_calendar.py  →  claude_writer.py  →  elevenlabs_music.py  →  video_builder.py  →  youtube_uploader.py
  (pick topic)            (write script)        (voice MP3 via TTS)    (FFmpeg video×2)     (upload both)
```

1. **content_calendar.py** — picks today's content type (learning / song / movement / story) and rotates through topic pools. Seasonal overrides for Christmas, Halloween, Valentine's Day, etc.
2. **claude_writer.py** — calls `claude-opus-4-5` to write lyrics, a full video script with `[VISUAL: ...]` markers, title, description, and tags.
3. **elevenlabs_music.py** — generates voice narration via ElevenLabs TTS (`eleven_multilingual_v2`), downloads MP3.
4. **video_builder.py** — renders an animated video locally using FFmpeg: animated gradient background, title text, bouncing ♪♫ notes, timed lyrics. Outputs 1280×720 main video and 720×1280 Short (first 60s). No external API.
5. **youtube_uploader.py** — uploads both videos via YouTube Data API v3 with `madeForKids=True`.
6. **utils.py** — centralised logging (daily log files) and output-folder cleanup.

---

## Weekly schedule

| Day       | Content type       |
|-----------|--------------------|
| Monday    | Learning video     |
| Tuesday   | Kids song          |
| Wednesday | Learning video     |
| Thursday  | Movement & dance   |
| Friday    | Kids song          |
| Saturday  | Story time         |
| Sunday    | Movement & dance   |
| **Daily** | YouTube Short      |

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/pmac789/MCP-Youtube-Automate.git
cd MCP-Youtube-Automate
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

FFmpeg must be installed locally for development (`brew install ffmpeg` on macOS). On Railway it is installed automatically via `nixPackages = ["ffmpeg"]` in `railway.toml`.

### 2. Create accounts & get API keys

**ElevenLabs** — elevenlabs.io
- Sign up → Creator plan ($11/mo)
- Profile → API Keys → create key → copy as `ELEVENLABS_API_KEY`
- Voices → pick a kids-friendly voice → copy the Voice ID as `ELEVENLABS_VOICE_ID`

**Claude** — console.anthropic.com
- API Keys → create key → copy as `ANTHROPIC_API_KEY`

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in all keys
```

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `ELEVENLABS_API_KEY` | elevenlabs.io → Profile → API Keys |
| `ELEVENLABS_VOICE_ID` | elevenlabs.io → Voices → pick voice → copy ID |
| `YT_PRIVACY` | `public`, `unlisted`, or `private` (default: `private`) |
| `YOUTUBE_TOKEN_B64` | Output of `python auth_setup.py` — base64-encoded token.pickle |

### 4. YouTube OAuth (one-time, local)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Desktop app)
3. Download JSON → save as `client_secrets.json` in the project root
4. Run: `python auth_setup.py` — opens a browser to authorise, then prints a `YOUTUBE_TOKEN_B64` value
5. Copy that value into Railway as the `YOUTUBE_TOKEN_B64` environment variable
6. On Railway, the bot decodes it automatically at startup — no file mounting needed

### 5. Run locally

```bash
python main.py          # starts the scheduler; fires daily at 09:00 UTC
FORCE_RUN=true python main.py  # run pipeline immediately on startup, then schedule
```

---

## Deploy to Railway

1. Push this repo to GitHub
2. Create a new Railway project → connect the GitHub repo
3. Add all 5 environment variables from `.env.example` (including `YOUTUBE_TOKEN_B64`)
4. Railway uses `railway.toml` — it will run `python main.py` automatically
5. FFmpeg is installed automatically via `nixPackages = ["ffmpeg"]` in `railway.toml`
6. No file mounting needed — `token.pickle` is decoded from `YOUTUBE_TOKEN_B64` at startup

---

## Project structure

```
MCP-Youtube-Automate/
├── main.py                 — scheduler + pipeline orchestrator
├── content_calendar.py     — weekly schedule & topic rotation
├── claude_writer.py        — Claude AI content writing
├── elevenlabs_music.py     — ElevenLabs TTS voice narration
├── video_builder.py        — local FFmpeg animated video renderer
├── youtube_uploader.py     — YouTube Data API v3 uploader
├── auth_setup.py           — one-time OAuth token generator
├── utils.py                — logging + cleanup utilities
├── requirements.txt
├── railway.toml
├── .env.example
├── .gitignore
├── CHANGELOG.md            — full project history
├── logs/                   — daily log files (gitignored)
└── output/                 — temp audio/video files (gitignored)
```

---

## Security notes

- Never commit `.env`, `token.pickle`, or `client_secrets.json`
- All secrets are loaded from environment variables via `python-dotenv`
- `token.pickle` should be treated as a credential — rotate if compromised
- All `*.json` files are gitignored to prevent accidental credential commits
