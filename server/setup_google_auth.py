"""
Google OAuth Setup for Aria MCP
Run this once to authenticate with Google services
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import json

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets'
]

def setup_google_auth():
    """Setup Google OAuth credentials."""
    creds = None
    
    # Check if we already have credentials
    if os.path.exists('google_credentials.json'):
        creds = Credentials.from_authorized_user_file('google_credentials.json', SCOPES)
    
    # If there are no (valid) credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # You need to download client_secret.json from Google Cloud Console
            if not os.path.exists('client_secret.json'):
                print("❌ ERROR: client_secret.json not found!")
                print("\n📋 Setup Instructions:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project or select existing")
                print("3. Enable these APIs:")
                print("   - Google Drive API")
                print("   - Gmail API")
                print("   - Google Calendar API")
                print("   - Google Sheets API")
                print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client ID'")
                print("5. Application type: Desktop app")
                print("6. Download the JSON and save as 'client_secret.json' in this folder")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('google_credentials.json', 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Google authentication successful!")
        print("Credentials saved to google_credentials.json")
        return True
    
    print("✅ Already authenticated with Google!")
    return True

if __name__ == "__main__":
    print("🔐 Aria MCP — Google OAuth Setup\n")
    setup_google_auth()
