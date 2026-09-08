"""
gaia/gaia_google.py — Big Sister GAIA Google Ecosystem Integration
Connects Big Sister GAIA to the shared Google Account: aviirrll@gmail.com
Services Enabled:
  • Google Drive (Cloud Vaulting, Snapshots, Code Reviews)
  • Gmail (Supervisory Alerts & Turn Summaries)
  • Google Calendar (Evolution & Maintenance Schedules)
  • Google Sheets (RL Scores & Audit Ledgers)
  • YouTube Data API (Research & Media Management)
"""

import os
import sys
import base64
from email.mime.text import MIMEText
from typing import Dict, Any, List, Tuple, Optional

# Paths
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from core.paths import CONFIG_DIR
from gaia.gaia_bus import bus

# Shared credentials directory
GOOGLE_ACCOUNT_DIR = os.path.join(CONFIG_DIR, "aria_gaia_google_account")
GOOGLE_CREDS_FILE = os.path.join(GOOGLE_ACCOUNT_DIR, "google_credentials.json")


class GaiaGoogleEngine:
    def __init__(self, creds_path: str = GOOGLE_CREDS_FILE):
        self.creds_path = creds_path
        self._credentials = None
        self._services = {}

    def get_credentials(self):
        """Loads and refreshes OAuth credentials for aviirrll@gmail.com."""
        if not os.path.exists(self.creds_path):
            return None
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            if self._credentials is None:
                self._credentials = Credentials.from_authorized_user_file(self.creds_path)

            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
            return self._credentials
        except Exception as e:
            bus.emit("GAIA", "GOOGLE_AUTH_ERROR", f"Failed to load credentials: {e}")
            return None

    def get_service(self, service_name: str, version: str):
        """Returns authenticated Google API client service."""
        key = f"{service_name}_{version}"
        if key in self._services:
            return self._services[key]

        creds = self.get_credentials()
        if not creds:
            return None

        try:
            from googleapiclient.discovery import build
            service = build(service_name, version, credentials=creds, cache_discovery=False)
            self._services[key] = service
            return service
        except Exception as e:
            bus.emit("GAIA", "GOOGLE_SERVICE_ERROR", f"Failed to build {service_name} {version}: {e}")
            return None

    # ── 1. GOOGLE DRIVE: CLOUD VAULTING & STORAGE ────────────────────────────
    def upload_to_drive(self, local_path: str, drive_folder_name: str = "GAIA_Aria_Vault") -> Tuple[bool, str]:
        """Uploads a local file to Google Drive under drive_folder_name."""
        drive = self.get_service("drive", "v3")
        if not drive:
            return False, "Google Drive service unavailable."

        if not os.path.exists(local_path):
            return False, f"Local file '{local_path}' does not exist."

        try:
            from googleapiclient.http import MediaFileUpload

            # Find or create target folder
            folder_id = None
            q = f"name = '{drive_folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res = drive.files().list(q=q, fields="files(id, name)").execute()
            files = res.get("files", [])
            if files:
                folder_id = files[0]["id"]
            else:
                meta = {"name": drive_folder_name, "mimeType": "application/vnd.google-apps.folder"}
                f = drive.files().create(body=meta, fields="id").execute()
                folder_id = f.get("id")

            # Upload file
            filename = os.path.basename(local_path)
            file_meta = {"name": filename}
            if folder_id:
                file_meta["parents"] = [folder_id]

            media = MediaFileUpload(local_path, resumable=True)
            uploaded = drive.files().create(body=file_meta, media_body=media, fields="id, name, webViewLink").execute()

            link = uploaded.get("webViewLink", "")
            msg = f"Uploaded '{filename}' to Google Drive [{drive_folder_name}]. ID: {uploaded.get('id')}"
            bus.emit("GAIA", "DRIVE_UPLOAD", msg, {"file": filename, "link": link})
            return True, msg
        except Exception as e:
            err = f"Failed to upload '{local_path}' to Google Drive: {e}"
            bus.emit("GAIA", "DRIVE_ERROR", err)
            return False, err

    def list_drive_files(self, page_size: int = 15) -> List[Dict[str, Any]]:
        """Lists recent files from Google Drive."""
        drive = self.get_service("drive", "v3")
        if not drive:
            return []
        try:
            res = drive.files().list(pageSize=page_size, fields="files(id, name, mimeType, modifiedTime)").execute()
            return res.get("files", [])
        except Exception as e:
            bus.emit("GAIA", "DRIVE_LIST_ERROR", str(e))
            return []

    # ── 2. GMAIL: SUPERVISORY NOTIFICATIONS & ALERTS ────────────────────────
    def send_email(self, subject: str, body_text: str, recipient: str = "aviirrll@gmail.com") -> Tuple[bool, str]:
        """Sends an email alert from aviirrll@gmail.com."""
        gmail = self.get_service("gmail", "v1")
        if not gmail:
            return False, "Gmail service unavailable."

        try:
            message = MIMEText(body_text)
            message["to"] = recipient
            message["from"] = "aviirrll@gmail.com"
            message["subject"] = f"👩‍🏫 [GAIA Supervisor] {subject}"

            raw_b64 = base64.urlsafe_b64encode(message.as_bytes()).decode()
            sent = gmail.users().messages().send(userId="me", body={"raw": raw_b64}).execute()

            msg_id = sent.get("id", "unknown")
            info = f"Sent email '{subject}' to {recipient} (Message ID: {msg_id})"
            bus.emit("GAIA", "EMAIL_SENT", info)
            return True, info
        except Exception as e:
            err = f"Failed to send email via Gmail API: {e}"
            bus.emit("GAIA", "EMAIL_ERROR", err)
            return False, err

    def get_unread_count(self) -> int:
        """Returns count of unread emails in inbox."""
        gmail = self.get_service("gmail", "v1")
        if not gmail:
            return 0
        try:
            res = gmail.users().messages().list(userId="me", q="is:unread label:INBOX").execute()
            return len(res.get("messages", []))
        except Exception:
            return 0

    # ── 3. GOOGLE CALENDAR: EVOLUTION & MAINTENANCE SCHEDULES ───────────────
    def list_upcoming_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetches upcoming calendar events."""
        cal = self.get_service("calendar", "v3")
        if not cal:
            return []
        try:
            import datetime
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events = cal.events().list(calendarId="primary", timeMin=now, maxResults=max_results, singleEvents=True, orderBy="startTime").execute()
            return events.get("items", [])
        except Exception as e:
            bus.emit("GAIA", "CALENDAR_ERROR", str(e))
            return []

    def create_calendar_event(self, summary: str, start_time: str, end_time: str, description: str = "") -> Tuple[bool, str]:
        """Creates an event on Google Calendar."""
        cal = self.get_service("calendar", "v3")
        if not cal:
            return False, "Google Calendar service unavailable."
        try:
            event = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_time, "timeZone": "UTC"},
                "end": {"dateTime": end_time, "timeZone": "UTC"}
            }
            res = cal.events().insert(calendarId="primary", body=event).execute()
            event_id = res.get("id", "unknown")
            msg = f"Created Calendar Event '{summary}' [{start_time} - {end_time}] (ID: {event_id})"
            bus.emit("GAIA", "CALENDAR_EVENT_CREATED", msg, {"id": event_id, "summary": summary})
            return True, msg
        except Exception as e:
            err = f"Failed to create calendar event: {e}"
            bus.emit("GAIA", "CALENDAR_ERROR", err)
            return False, err

    # ── 4. GOOGLE SHEETS: RL SCORES & AUDIT LEDGERS ─────────────────────────
    def create_sheet(self, title: str) -> Tuple[bool, str, str]:
        """Creates a new Google Spreadsheet."""
        sheets = self.get_service("sheets", "v4")
        if not sheets:
            return False, "Google Sheets service unavailable.", ""
        try:
            body = {"properties": {"title": title}}
            res = sheets.spreadsheets().create(body=body).execute()
            sheet_id = res.get("spreadsheetId", "")
            msg = f"Created spreadsheet '{title}' (ID: {sheet_id})"
            bus.emit("GAIA", "SHEET_CREATED", msg, {"id": sheet_id, "title": title})
            return True, msg, sheet_id
        except Exception as e:
            err = f"Failed to create spreadsheet: {e}"
            bus.emit("GAIA", "SHEETS_ERROR", err)
            return False, err, ""

    def append_to_sheet(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> Tuple[bool, str]:
        """Appends rows to a Google Spreadsheet."""
        sheets = self.get_service("sheets", "v4")
        if not sheets:
            return False, "Google Sheets service unavailable."
        try:
            body = {"values": values}
            res = sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            updates = res.get("updates", {})
            updated_rows = updates.get("updatedRows", len(values))
            msg = f"Appended {updated_rows} rows to sheet {spreadsheet_id}"
            bus.emit("GAIA", "SHEET_APPENDED", msg)
            return True, msg
        except Exception as e:
            err = f"Failed to append to sheet: {e}"
            bus.emit("GAIA", "SHEETS_ERROR", err)
            return False, err

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """Reads rows from a Google Spreadsheet."""
        sheets = self.get_service("sheets", "v4")
        if not sheets:
            return []
        try:
            res = sheets.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
            return res.get("values", [])
        except Exception as e:
            bus.emit("GAIA", "SHEETS_ERROR", str(e))
            return []

    # ── 5. YOUTUBE: RESEARCH & MEDIA INSPECTION ──────────────────────────────
    def search_youtube(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Searches YouTube videos."""
        yt = self.get_service("youtube", "v3")
        if not yt:
            return []
        try:
            res = yt.search().list(q=query, part="snippet", maxResults=max_results, type="video").execute()
            items = []
            for item in res.get("items", []):
                snippet = item.get("snippet", {})
                items.append({
                    "title": snippet.get("title"),
                    "videoId": item.get("id", {}).get("videoId"),
                    "channelTitle": snippet.get("channelTitle"),
                    "description": snippet.get("description"),
                })
            return items
        except Exception as e:
            bus.emit("GAIA", "YOUTUBE_ERROR", str(e))
            return []


# Global Singleton for GAIA
gaia_google = GaiaGoogleEngine()

