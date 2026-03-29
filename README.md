# MCP-Youtube-Automate — Happy Melody Kids

Fully automated YouTube content pipeline for the **Happy Melody Kids** channel (ages 1–6).
Runs daily at 09:00 UTC, generating a full-length video **and** a YouTube Short from scratch using AI.

---

## Pipeline overview

```
content_calendar.py  →  claude_writer.py  →  suno_music.py  →  pictory_video.py  →  youtube_uploader.py
  (pick topic)            (write script)       (generate MP3)     (render MP4×2)       (upload both)
```

1. **content_calendar.py** — picks today's content type (learning / song / movement / story) and rotates through topic pools. Seasonal overrides for Christmas, Halloween, Valentine's Day, etc.
2. **claude_writer.py** — calls `claude-opus-4-5` to write lyrics, a full video script with `[VISUAL: ...]` markers, title, description, and tags.
3. **suno_music.py** — submits lyrics to Suno AI, polls until the track is ready, downloads the MP3.
4. **pictory_video.py** — sends script + audio to Pictory AI, renders a 16:9 main video and a 9:16 Short, downloads both.
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

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `SUNO_API_KEY` | app.suno.ai → API settings |
| `PICTORY_API_KEY` | pictory.ai → API settings |
| `PICTORY_CLIENT_ID` | pictory.ai → API settings |
| `YT_PRIVACY` | `public`, `unlisted`, or `private` |

### 3. YouTube OAuth (one-time, local)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Desktop app)
3. Download JSON → save as `client_secrets.json` in the project root
4. Run: `python auth_setup.py` — this opens a browser to authorise and saves `token.pickle`
5. Upload `token.pickle` to Railway as a secret file (do **not** commit it)

### 4. Run locally

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
├── suno_music.py           — Suno AI music generation
├── pictory_video.py        — Pictory AI video rendering
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
