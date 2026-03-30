# MCP-Youtube-Automate — Happy Melody Kids

Fully automated YouTube content pipeline for the **Happy Melody Kids** channel (ages 1–6).
Runs daily at 09:00 UTC, generating a full-length video **and** a YouTube Short from scratch using AI.

---

## Stack & cost

| Service       | Purpose                          | Cost     |
|---------------|----------------------------------|----------|
| Claude API    | Writes scripts + lyrics          | ~$8/mo   |
| ElevenLabs    | Music + voice narration          | $11/mo   |
| HeyGen        | Animated character video         | $29/mo   |
| Railway       | Hosts the bot 24/7               | $5/mo    |
| **Total**     |                                  | **~$53/mo** |

---

## Pipeline overview

```
content_calendar.py  →  claude_writer.py  →  elevenlabs_music.py  →  heygen_video.py  →  youtube_uploader.py
  (pick topic)            (write script)      (music + voice MP3)     (avatar video×2)     (upload both)
```

1. **content_calendar.py** — picks today's content type (learning / song / movement / story) and rotates through topic pools. Seasonal overrides for Christmas, Halloween, Valentine's Day, etc.
2. **claude_writer.py** — calls `claude-opus-4-5` to write lyrics, a full video script with `[VISUAL: ...]` markers, title, description, and tags.
3. **elevenlabs_music.py** — generates a full kids song via ElevenLabs Music Generation API, polls until done, downloads MP3. Also provides `generate_voiceover()` for TTS narration.
4. **heygen_video.py** — uploads MP3 to HeyGen, renders a lip-synced avatar video at 1920×1080 (main) and 1080×1920 (Short), downloads both MP4s.
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

### 2. Create accounts & get API keys

**ElevenLabs** — elevenlabs.io
- Sign up → Creator plan ($11/mo)
- Profile → API Keys → create key → copy as `ELEVENLABS_API_KEY`
- Voices → pick a kids-friendly voice → copy the Voice ID as `ELEVENLABS_VOICE_ID`

**HeyGen** — app.heygen.com
- Sign up → Creator plan ($29/mo)
- Settings → API → generate key → copy as `HEYGEN_API_KEY`
- Avatars → pick a cartoon character avatar → copy the Avatar ID as `HEYGEN_AVATAR_ID`

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
| `HEYGEN_API_KEY` | app.heygen.com → Settings → API |
| `HEYGEN_AVATAR_ID` | app.heygen.com → Avatars → pick avatar → copy ID (default: `823e02e85726482c80bfff9d6baceb4d`) |
| `YT_PRIVACY` | `public`, `unlisted`, or `private` (default: `private`) |

### 4. YouTube OAuth (one-time, local)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Desktop app)
3. Download JSON → save as `client_secrets.json` in the project root
4. Run: `python auth_setup.py` — opens a browser to authorise, saves `token.pickle`
5. Upload `token.pickle` to Railway as a secret file (do **not** commit it)

### 5. Run locally

```bash
python main.py          # starts the scheduler; fires daily at 09:00 UTC
```

---

## Deploy to Railway

1. Push this repo to GitHub
2. Create a new Railway project → connect the GitHub repo
3. Add all environment variables from `.env.example`
4. Mount `token.pickle` as a volume or secret file at `/app/token.pickle`
5. Railway uses `railway.toml` — it will run `python main.py` automatically

---

## Project structure

```
MCP-Youtube-Automate/
├── main.py                 — scheduler + pipeline orchestrator
├── content_calendar.py     — weekly schedule & topic rotation
├── claude_writer.py        — Claude AI content writing
├── elevenlabs_music.py     — ElevenLabs music generation + TTS voiceover
├── heygen_video.py         — HeyGen avatar lip-sync video rendering
├── youtube_uploader.py     — YouTube Data API v3 uploader
├── auth_setup.py           — one-time OAuth token generator
├── utils.py                — logging + cleanup utilities
├── requirements.txt
├── railway.toml
├── .env.example
├── .gitignore
├── logs/                   — daily log files (gitignored)
└── output/                 — temp audio/video files (gitignored)
```

---

## Security notes

- Never commit `.env`, `token.pickle`, or `client_secrets.json`
- All secrets are loaded from environment variables via `python-dotenv`
- `token.pickle` should be treated as a credential — rotate if compromised
