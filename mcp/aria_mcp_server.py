"""
Aria MCP Server — Custom Model Context Protocol implementation
Security-first design with explicit user permission for every action
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# MCP protocol implementation
class AriaMCPServer:
    def __init__(self):
        self.tools = self._register_tools()
        self.audit_log = []
        self.config = self._load_config()
        
    def _load_config(self):
        """Load security config and API credentials."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(base_dir)
        cfg_candidates = [
            os.path.join(base_dir, "aria_mcp_config.json"),
            os.path.join(root_dir, "config", "aria_mcp_config.json"),
            os.path.join(root_dir, "aria_mcp_config.json"),
        ]
        for cp in cfg_candidates:
            if os.path.exists(cp):
                with open(cp, encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg

        creds_path = os.path.join(root_dir, "config", "google_credentials.json")
        if not os.path.exists(creds_path):
            creds_path = os.path.join(root_dir, "google_credentials.json")

        return {
            "google_credentials_path": creds_path,
            "allowed_local_paths": [os.path.join(root_dir, "data", "knowledge")],
            "gmail_whitelist": [],  # Empty = allow all
            "drive_whitelist": [],  # Empty = allow all
            "max_file_size_mb": 10,
            "audit_log_path": os.path.join(root_dir, "aria_mcp_audit.log")
        }
    
    def _register_tools(self):
        """Register all available MCP tools."""
        return {
            # Google Drive
            "drive_search": {
                "description": "Search for files in Google Drive",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "handler": self._drive_search
            },
            "drive_read": {
                "description": "Read content of a Google Drive file",
                "parameters": {
                    "file_id": {"type": "string", "description": "File ID"}
                },
                "handler": self._drive_read
            },
            "drive_create": {
                "description": "Create a new file in Google Drive",
                "parameters": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                    "mime_type": {"type": "string"}
                },
                "handler": self._drive_create
            },
            
            # Gmail
            "gmail_search": {
                "description": "Search emails in Gmail",
                "parameters": {
                    "query": {"type": "string", "description": "Search query (e.g., 'from:user@example.com')"}
                },
                "handler": self._gmail_search
            },
            "gmail_read": {
                "description": "Read a specific email",
                "parameters": {
                    "message_id": {"type": "string"}
                },
                "handler": self._gmail_read
            },
            "gmail_send": {
                "description": "Send an email",
                "parameters": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "handler": self._gmail_send
            },
            
            # Google Calendar
            "calendar_list": {
                "description": "List upcoming calendar events",
                "parameters": {
                    "max_results": {"type": "integer", "default": 10}
                },
                "handler": self._calendar_list
            },
            "calendar_create": {
                "description": "Create a calendar event",
                "parameters": {
                    "summary": {"type": "string"},
                    "start": {"type": "string", "description": "ISO datetime"},
                    "end": {"type": "string", "description": "ISO datetime"}
                },
                "handler": self._calendar_create
            },
            
            # Google Sheets
            "sheets_read": {
                "description": "Read data from Google Sheets",
                "parameters": {
                    "spreadsheet_id": {"type": "string"},
                    "range": {"type": "string", "description": "e.g., 'Sheet1!A1:D10'"}
                },
                "handler": self._sheets_read
            },
            "sheets_write": {
                "description": "Write data to Google Sheets",
                "parameters": {
                    "spreadsheet_id": {"type": "string"},
                    "range": {"type": "string"},
                    "values": {"type": "array"}
                },
                "handler": self._sheets_write
            },
            
            # Local Files
            "file_read": {
                "description": "Read a local file (restricted to allowed paths)",
                "parameters": {
                    "path": {"type": "string"}
                },
                "handler": self._file_read
            },
            "file_write": {
                "description": "Write to a local file (restricted)",
                "parameters": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "handler": self._file_write
            },
            "file_list": {
                "description": "List files in a directory",
                "parameters": {
                    "path": {"type": "string"}
                },
                "handler": self._file_list
            }
        }
    
    # ═══ PERMISSION SYSTEM ═══════════════════════════════════════════
    
    def _request_permission(self, action, details):
        """
        Ask user for permission via GUI dialog.
        Returns True if approved, False if denied.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log the request
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details,
            "status": "PENDING"
        }
        
        # Send permission request to stdout (Aria will parse this)
        request = {
            "type": "permission_request",
            "action": action,
            "details": details,
            "timestamp": timestamp
        }
        
        print(json.dumps(request), flush=True)
        
        # Wait for response on stdin
        try:
            response_line = sys.stdin.readline()
            response = json.loads(response_line)
            
            approved = response.get("approved", False)
            log_entry["status"] = "APPROVED" if approved else "DENIED"
            log_entry["user_response"] = response.get("reason", "")
            
            self._log_audit(log_entry)
            return approved
            
        except Exception as e:
            log_entry["status"] = "ERROR"
            log_entry["error"] = str(e)
            self._log_audit(log_entry)
            return False
    
    def _log_audit(self, entry):
        """Write to audit log."""
        log_path = self.config.get("audit_log_path", "./aria_mcp_audit.log")
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.audit_log.append(entry)
    
    # ═══ GOOGLE DRIVE HANDLERS ═══════════════════════════════════════
    
    def _drive_search(self, query):
        """Search Google Drive."""
        if not self._request_permission("drive_search", {"query": query}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/drive.readonly']
            )
            
            service = build('drive', 'v3', credentials=creds)
            results = service.files().list(
                q=query,
                pageSize=10,
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            return {"files": results.get('files', [])}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _drive_read(self, file_id):
        """Read Google Drive file content."""
        if not self._request_permission("drive_read", {"file_id": file_id}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            import io
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/drive.readonly']
            )
            
            service = build('drive', 'v3', credentials=creds)
            
            # Get file metadata
            file_meta = service.files().get(fileId=file_id).execute()
            
            # Download content
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            from googleapiclient.http import MediaIoBaseDownload
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            content = fh.getvalue().decode('utf-8')
            
            return {
                "name": file_meta.get("name"),
                "content": content,
                "mime_type": file_meta.get("mimeType")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _drive_create(self, name, content, mime_type):
        """Create new file in Google Drive."""
        if not self._request_permission("drive_create", 
                                       {"name": name, "size": len(content)}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from googleapiclient.http import MediaInMemoryUpload
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/drive.file']
            )
            
            service = build('drive', 'v3', credentials=creds)
            
            file_metadata = {'name': name}
            media = MediaInMemoryUpload(
                content.encode('utf-8'),
                mimetype=mime_type
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {"file": file}
            
        except Exception as e:
            return {"error": str(e)}
    
    # ═══ GMAIL HANDLERS ═══════════════════════════════════════════════
    
    def _gmail_search(self, query):
        """Search Gmail."""
        if not self._request_permission("gmail_search", {"query": query}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/gmail.readonly']
            )
            
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()
            
            return {"messages": results.get('messages', [])}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _gmail_read(self, message_id):
        """Read Gmail message."""
        if not self._request_permission("gmail_read", {"message_id": message_id}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            import base64
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/gmail.readonly']
            )
            
            service = build('gmail', 'v1', credentials=creds)
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Parse headers
            headers = {}
            for h in message['payload'].get('headers', []):
                headers[h['name']] = h['value']
            
            # Get body
            body = ""
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
            
            return {
                "subject": headers.get('Subject', ''),
                "from": headers.get('From', ''),
                "date": headers.get('Date', ''),
                "body": body
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _gmail_send(self, to, subject, body):
        """Send email via Gmail."""
        if not self._request_permission("gmail_send", 
                                       {"to": to, "subject": subject}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from email.mime.text import MIMEText
            import base64
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/gmail.send']
            )
            
            service = build('gmail', 'v1', credentials=creds)
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            return {"message_id": result['id'], "status": "sent"}
            
        except Exception as e:
            return {"error": str(e)}
    
    # ═══ CALENDAR HANDLERS ════════════════════════════════════════════
    
    def _calendar_list(self, max_results=10):
        """List upcoming calendar events."""
        if not self._request_permission("calendar_list", {"max_results": max_results}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from datetime import datetime, timezone
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/calendar.readonly']
            )
            
            service = build('calendar', 'v3', credentials=creds)
            
            now = datetime.now(timezone.utc).isoformat()
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return {"events": events_result.get('items', [])}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calendar_create(self, summary, start, end):
        """Create calendar event."""
        if not self._request_permission("calendar_create",
                                       {"summary": summary, "start": start}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/calendar']
            )
            
            service = build('calendar', 'v3', credentials=creds)
            
            event = {
                'summary': summary,
                'start': {'dateTime': start, 'timeZone': 'UTC'},
                'end': {'dateTime': end, 'timeZone': 'UTC'}
            }
            
            result = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {"event": result}
            
        except Exception as e:
            return {"error": str(e)}
    
    # ═══ SHEETS HANDLERS ══════════════════════════════════════════════
    
    def _sheets_read(self, spreadsheet_id, range):
        """Read from Google Sheets."""
        if not self._request_permission("sheets_read",
                                       {"spreadsheet_id": spreadsheet_id, "range": range}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            
            service = build('sheets', 'v4', credentials=creds)
            
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range
            ).execute()
            
            return {"values": result.get('values', [])}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _sheets_write(self, spreadsheet_id, range, values):
        """Write to Google Sheets."""
        if not self._request_permission("sheets_write",
                                       {"spreadsheet_id": spreadsheet_id,
                                        "range": range,
                                        "rows": len(values)}):
            return {"error": "Permission denied"}
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            creds = Credentials.from_authorized_user_file(
                self.config["google_credentials_path"],
                ['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=creds)
            
            body = {'values': values}
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return {"updated_cells": result.get('updatedCells')}
            
        except Exception as e:
            return {"error": str(e)}
    
    # ═══ LOCAL FILE HANDLERS ══════════════════════════════════════════
    
    def _is_path_allowed(self, path):
        """Check if path is within allowed directories."""
        path = Path(path).resolve()
        allowed = self.config.get("allowed_local_paths", [])
        
        for allowed_path in allowed:
            if path.is_relative_to(Path(allowed_path).resolve()):
                return True
        return False
    
    def _file_read(self, path):
        """Read local file."""
        if not self._is_path_allowed(path):
            return {"error": "Path not in allowed directories"}
        
        if not self._request_permission("file_read", {"path": path}):
            return {"error": "Permission denied"}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content, "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    def _file_write(self, path, content):
        """Write local file."""
        if not self._is_path_allowed(path):
            return {"error": "Path not in allowed directories"}
        
        if not self._request_permission("file_write",
                                       {"path": path, "size": len(content)}):
            return {"error": "Permission denied"}
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    def _file_list(self, path):
        """List files in directory."""
        if not self._is_path_allowed(path):
            return {"error": "Path not in allowed directories"}
        
        if not self._request_permission("file_list", {"path": path}):
            return {"error": "Permission denied"}
        
        try:
            path_obj = Path(path)
            files = []
            for item in path_obj.iterdir():
                files.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}
    
    # ═══ MCP PROTOCOL ═════════════════════════════════════════════════
    
    def handle_request(self, request):
        """Handle MCP protocol request."""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "tools": [
                    {"name": name, **info}
                    for name, info in self.tools.items()
                ]
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_params = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return {"error": f"Unknown tool: {tool_name}"}
            
            handler = self.tools[tool_name]["handler"]
            result = handler(**tool_params)
            
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        
        else:
            return {"error": f"Unknown method: {method}"}
    
    def run(self):
        """Main MCP server loop."""
        print(json.dumps({"type": "server_ready"}), flush=True)
        
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except Exception as e:
                error_response = {"error": str(e)}
                print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    server = AriaMCPServer()
    server.run()
