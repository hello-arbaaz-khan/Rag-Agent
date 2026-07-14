"""
One-time OAuth authentication script.

Run this script ONCE from a terminal that has access to a web browser:
    cd drive_service/
    python auth.py

It will:
1. Open a browser tab asking you to log in and grant Drive access.
2. Write the resulting token (access + refresh) to token.json.
3. Exit.

After running this, restart the FastAPI server:
    uvicorn main:app --reload --port 8001

You only need to re-run this if the refresh token expires
(Google OAuth "Testing" mode: refresh tokens expire after 7 days;
 "Production" mode: refresh tokens do NOT expire unless revoked).
"""

import os
import sys

# Make sure we can import config from the same directory
sys.path.insert(0, os.path.dirname(__file__))

from google_auth_oauthlib.flow import InstalledAppFlow
from config import settings


def main():
    print("Starting OAuth flow — your browser will open shortly...")
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.google_credentials_file,
        settings.google_drive_scopes,
    )
    creds = flow.run_local_server(port=0)

    with open(settings.google_token_file, "w") as token_file:
        token_file.write(creds.to_json())

    print(f"\n✅ Authentication successful!")
    print(f"   Token saved to: {settings.google_token_file}")
    print(f"   Restart the FastAPI server to pick up the new token.\n")


if __name__ == "__main__":
    main()
