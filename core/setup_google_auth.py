"""
core/setup_google_auth.py — Google OAuth Setup for Aria & GAIA
Supports:
  1. Default Master profile: config/client_secret.json -> config/google_credentials.json
  2. Dedicated Aria & GAIA profile: config/aria_gaia_google_account/
"""
import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from core.paths import CONFIG_DIR

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/youtube'
]

ARIA_GAIA_DIR = os.path.join(CONFIG_DIR, "aria_gaia_google_account")

def setup_google_auth(profile: str = "aria"):
    """
    Setup Google OAuth credentials.
    profile="aria": stores in config/aria_gaia_google_account/
    profile="master": stores in config/
    """
    if profile.lower() in ("aria", "gaia", "aviirrll"):
        target_dir = ARIA_GAIA_DIR
        secret_file = os.path.join(target_dir, "client_secret.json")
        creds_file = os.path.join(target_dir, "google_credentials.json")
        account_label = "Aria & GAIA (aviirrll@gmail.com)"
    else:
        target_dir = CONFIG_DIR
        secret_file = os.path.join(CONFIG_DIR, "client_secret.json")
        creds_file = os.path.join(CONFIG_DIR, "google_credentials.json")
        account_label = "Master System Account"

    os.makedirs(target_dir, exist_ok=True)
    creds = None

    if os.path.exists(creds_file):
        try:
            creds = Credentials.from_authorized_user_file(creds_file, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"🔄 Refreshing token for {account_label}...")
            creds.refresh(Request())
        else:
            if not os.path.exists(secret_file):
                print(f"❌ ERROR: {secret_file} not found!")
                print(f"\n📋 Setup Instructions for {account_label}:")
                print("1. Download the OAuth Client ID JSON from your new Aria-Gaia Google Cloud project.")
                print(f"2. Save it as: {secret_file}")
                return False

            print(f"🌐 Launching browser authentication for {account_label}...")
            flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(creds_file, 'w', encoding="utf-8") as token:
            token.write(creds.to_json())

        print(f"✅ Google authentication successful for {account_label}!")
        print(f"Credentials safely saved to {creds_file}")
        return True

    print(f"✅ Already authenticated with Google for {account_label}!")
    return True

if __name__ == "__main__":
    profile_arg = "aria" if len(sys.argv) < 2 else sys.argv[1].replace("--", "")
    print(f"🔐 Aria Google OAuth Setup — Profile: {profile_arg}\n")
    setup_google_auth(profile_arg)
