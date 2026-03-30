"""
auth_setup.py — One-time local script to generate token.pickle for YouTube OAuth2.

Run this once on your local machine (where a browser is available) before deploying.
It will open a browser window asking you to authorise the app, then print the
YOUTUBE_TOKEN_B64 value ready to paste into Railway as an environment variable.

Usage:
  python auth_setup.py
"""

import base64
import pickle
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SECRETS_FILE = Path(__file__).parent / "client_secrets.json"
TOKEN_FILE = Path(__file__).parent / "token.pickle"


def main() -> None:
    if not SECRETS_FILE.exists():
        print(
            "ERROR: client_secrets.json not found.\n"
            "Download it from Google Cloud Console → APIs & Services → Credentials.\n"
            "Save it as client_secrets.json in this folder, then re-run this script."
        )
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    # Encode to base64 for Railway env var
    b64 = base64.b64encode(TOKEN_FILE.read_bytes()).decode("utf-8")

    print("\n✅  token.pickle saved locally.")
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   Copy the value below into Railway as an environment variable:")
    print("   Variable name:  YOUTUBE_TOKEN_B64")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    print(b64)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("IMPORTANT: Never commit token.pickle or this value to git.")


if __name__ == "__main__":
    main()
