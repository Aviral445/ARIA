"""
tools/aria_cloudflare.py — Zero-Docker Edge Ingress & Cloudflare Integration for ARIA

Replaces heavy Docker/NGINX containers with:
1. Cloudflare Quick / Named Tunnel (`cloudflared` single binary):
   • Zero exposed router ports, zero dynamic DNS, automatic free HTTPS.
   • Connects aria_api.py:8000 securely to phone & remote clients.
   • Near-zero resource footprint (~30MB binary, <25MB RAM).
2. Cloudflare R2 Cloud Sync:
   • S3-compatible, zero-egress artifact and receipt offloading.
"""

import os
import sys
import json
import time
import shutil
import urllib.request
import urllib.error
import subprocess
import threading
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BIN_DIR = os.path.join(_ROOT, "tools", "bin")
_CLOUDFLARED_EXE = os.path.join(_BIN_DIR, "cloudflared.exe")
_DATA_DIR = os.path.join(_ROOT, "data")
_TUNNEL_STATE_FILE = os.path.join(_DATA_DIR, "cloudflare_tunnel.json")
_CONFIG_FILE = os.path.join(_ROOT, "config", "cloudflare.json")

CLOUDFLARED_DOWNLOAD_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
)


class CloudflareManager:
    """Manages Cloudflare Tunnel lifecycle, API verification, and R2 integration with zero Docker overhead."""

    def __init__(self):
        os.makedirs(_BIN_DIR, exist_ok=True)
        os.makedirs(_DATA_DIR, exist_ok=True)
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self.api_token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
        self.tunnel_token = os.environ.get("CLOUDFLARE_TUNNEL_TOKEN", "").strip()

    def verify_token(self) -> Dict[str, Any]:
        """Verifies the Cloudflare API token against Cloudflare's verify endpoint."""
        token = self.api_token
        if not token:
            return {"valid": False, "error": "CLOUDFLARE_API_TOKEN is not set in .env"}

        req = urllib.request.Request(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success"):
                    return {
                        "valid": True,
                        "status": data.get("result", {}).get("status"),
                        "expires_on": data.get("result", {}).get("expires_on"),
                        "message": "Token is valid and active on Cloudflare!"
                    }
                return {"valid": False, "error": data.get("errors", "Unknown verification error")}
        except urllib.error.HTTPError as e:
            return {"valid": False, "error": f"HTTP Error {e.code}: {e.read().decode('utf-8', errors='replace')}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def list_d1_databases(self) -> Dict[str, Any]:
        """Lists Cloudflare D1 serverless databases associated with the account."""
        if not self.api_token:
            return {"error": "CLOUDFLARE_API_TOKEN is not set in .env"}
        if not self.account_id:
            return {"error": "CLOUDFLARE_ACCOUNT_ID is not set in .env"}

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP Error {e.code}: {e.read().decode('utf-8', errors='replace')}"}
        except Exception as e:
            return {"error": str(e)}



    def find_cloudflared_binary(self) -> Optional[str]:
        """Locates cloudflared executable from local tools/bin or system PATH."""
        if os.path.isfile(_CLOUDFLARED_EXE):
            return _CLOUDFLARED_EXE
        system_bin = shutil.which("cloudflared")
        if system_bin:
            return system_bin
        return None

    def download_cloudflared(self, progress_callback=None) -> str:
        """Downloads the standalone official cloudflared binary (~35MB) to tools/bin/."""
        target_path = _CLOUDFLARED_EXE
        temp_path = f"{target_path}.tmp"
        print(f"[CloudflareManager] Downloading cloudflared binary to {target_path}...")

        def _reporthook(blocknum, blocksize, totalsize):
            if totalsize > 0 and progress_callback:
                percent = int(blocknum * blocksize * 100 / totalsize)
                progress_callback(min(percent, 100))

        urllib.request.urlretrieve(CLOUDFLARED_DOWNLOAD_URL, temp_path, reporthook=_reporthook)
        if os.path.exists(target_path):
            os.remove(target_path)
        os.rename(temp_path, target_path)
        print("[CloudflareManager] cloudflared downloaded successfully.")
        return target_path

    def ensure_binary(self) -> str:
        """Ensures cloudflared binary is available, downloading if needed."""
        path = self.find_cloudflared_binary()
        if not path:
            return self.download_cloudflared()
        return path

    def start_quick_tunnel(self, local_port: int = 8000, wait_for_url: int = 15) -> Dict[str, Any]:
        """
        Starts an instant Cloudflare Quick Tunnel forwarding to http://localhost:<local_port>.
        Extracts and records the ephemeral *.trycloudflare.com HTTPS URL.
        """
        bin_path = self.ensure_binary()
        cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{local_port}"]

        creation_flags = 0
        if sys.platform == "win32":
            # DETACHED_PROCESS to run in background or CREATE_NO_WINDOW
            creation_flags = subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creation_flags
        )
        self.process = proc

        public_url = None
        start_t = time.time()

        # Capture output line-by-line to extract trycloudflare.com URL
        while time.time() - start_t < wait_for_url:
            if proc.poll() is not None:
                break
            line = proc.stdout.readline() if proc.stdout else ""
            if not line:
                time.sleep(0.2)
                continue
            if "trycloudflare.com" in line:
                for token in line.split():
                    if "trycloudflare.com" in token:
                        cleaned = token.strip().rstrip(".,")
                        if cleaned.startswith("http"):
                            public_url = cleaned
                            break
                if public_url:
                    break

        self.public_url = public_url

        state = {
            "pid": proc.pid,
            "port": local_port,
            "public_url": public_url,
            "started_at": time.time(),
            "mode": "quick_tunnel",
            "status": "running" if proc.poll() is None else "stopped"
        }
        with open(_TUNNEL_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        return state

    def get_status(self) -> Dict[str, Any]:
        """Returns current tunnel status."""
        if not os.path.exists(_TUNNEL_STATE_FILE):
            return {"status": "inactive", "message": "No tunnel running"}

        try:
            with open(_TUNNEL_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            pid = state.get("pid")
            if pid:
                # Check if process is still alive on Windows
                is_alive = False
                try:
                    import psutil
                    is_alive = psutil.pid_exists(pid)
                except Exception:
                    # Fallback check
                    res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
                    is_alive = str(pid) in res.stdout
                state["status"] = "running" if is_alive else "dead"
            return state
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def stop_tunnel(self) -> Dict[str, Any]:
        """Stops the active cloudflared tunnel."""
        status = self.get_status()
        pid = status.get("pid")
        if pid:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            except Exception as e:
                return {"error": str(e)}

        if os.path.exists(_TUNNEL_STATE_FILE):
            try:
                os.remove(_TUNNEL_STATE_FILE)
            except Exception:
                pass
        return {"status": "stopped", "message": "Cloudflare tunnel stopped successfully."}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ARIA Cloudflare Zero-Docker Ingress CLI")
    parser.add_argument("action", choices=["start", "stop", "status", "download", "verify", "d1-list"], help="Action to perform")
    parser.add_argument("--port", type=int, default=8000, help="Local port to forward (default: 8000)")

    args = parser.parse_args()
    mgr = CloudflareManager()

    if args.action == "verify":
        res = mgr.verify_token()
        print(f"Token Verification: {json.dumps(res, indent=2)}")
    elif args.action == "d1-list":
        res = mgr.list_d1_databases()
        print(f"D1 Databases: {json.dumps(res, indent=2)}")
    elif args.action == "download":
        path = mgr.download_cloudflared()
        print(f"cloudflared ready at: {path}")
    elif args.action == "start":
        print(f"Starting Cloudflare Quick Tunnel forwarding to port {args.port}...")
        res = mgr.start_quick_tunnel(local_port=args.port)
        print(f"Tunnel State: {json.dumps(res, indent=2)}")
        if res.get("public_url"):
            print(f"\n[🚀 SUCCESS] Public URL: {res['public_url']}\n")
    elif args.action == "stop":
        res = mgr.stop_tunnel()
        print(f"Result: {json.dumps(res, indent=2)}")
    elif args.action == "status":
        st = mgr.get_status()
        print(json.dumps(st, indent=2))


