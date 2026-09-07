"""
aria_auth.py — Multi-Device Session Management & Master Admin Authentication for Aria
Handles:
- Master Admin authentication (Username: "L", Password: "balluboss")
- Device registration (Host Laptop vs Mobile/Client devices)
- Profile management and role-based permissions
- Session token generation & verification
"""

import os, json, time, hashlib, secrets, socket

try:
    from core.paths import get_config_file
except ImportError:
    try:
        from paths import get_config_file
    except ImportError:
        def get_config_file(fn): return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", fn)

AUTH_STORE_FILE = get_config_file("aria_auth.json")
MASTER_ADMIN_USER = os.getenv("ARIA_ADMIN_USER", "L")
MASTER_ADMIN_PASS = os.getenv("ARIA_ADMIN_PASSWORD", "balluboss")

# In-memory active sessions: { token: { "username": str, "role": "admin"|"user", "device": str, "created": float } }
_ACTIVE_SESSIONS = {}

def _hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _load_auth_store() -> dict:
    if os.path.exists(AUTH_STORE_FILE):
        try:
            with open(AUTH_STORE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Initialize default with Master Admin
    default_store = {
        "users": {
            MASTER_ADMIN_USER: {
                "password_hash": _hash_pass(MASTER_ADMIN_PASS),
                "role": "admin",
                "display_name": MASTER_ADMIN_USER,
                "is_master": True,
                "created": time.strftime("%Y-%m-%d")
            }
        },
        "devices": {
            "main_laptop": {
                "device_id": "main_laptop",
                "name": f"{socket.gethostname()} (Host PC)",
                "type": "master_host",
                "ip": "127.0.0.1",
                "last_seen": time.strftime("%Y-%m-%d %I:%M %p")
            }
        }
    }
    _save_auth_store(default_store)
    return default_store

def _save_auth_store(store: dict):
    try:
        with open(AUTH_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
    except Exception:
        pass

def authenticate_user(username: str, password: str, device_name: str = "Mobile Device") -> dict:
    """
    Authenticates a user. If username == "L" and password == "balluboss", grants Master Admin.
    Otherwise checks registered profile users or creates guest profile.
    """
    u_clean = username.strip()
    p_clean = password.strip()
    
    # 1. Master Admin verification
    if u_clean.lower() == MASTER_ADMIN_USER.lower() and p_clean == MASTER_ADMIN_PASS:
        token = "admin_" + secrets.token_hex(16)
        session_data = {
            "token": token,
            "username": "L",
            "role": "admin",
            "device": device_name,
            "is_admin": True,
            "created": time.time(),
            "expires_in_days": 30
        }
        _ACTIVE_SESSIONS[token] = session_data
        return {
            "success": True,
            "token": token,
            "username": "L",
            "role": "admin",
            "is_admin": True,
            "device_role": "Master Controller",
            "message": "👑 Master Admin session unlocked for L! Full multi-device control granted."
        }
        
    # 2. Check registered custom profiles
    store = _load_auth_store()
    user_rec = store.get("users", {}).get(u_clean)
    if user_rec:
        if user_rec.get("password_hash") == _hash_pass(p_clean):
            role = user_rec.get("role", "user")
            token = "usr_" + secrets.token_hex(16)
            session_data = {
                "token": token,
                "username": u_clean,
                "role": role,
                "device": device_name,
                "is_admin": (role == "admin"),
                "created": time.time()
            }
            _ACTIVE_SESSIONS[token] = session_data
            return {
                "success": True,
                "token": token,
                "username": u_clean,
                "role": role,
                "is_admin": (role == "admin"),
                "message": f"Logged in as profile '{u_clean}'."
            }
        else:
            return {"success": False, "message": "Invalid password for this profile."}
            
    return {"success": False, "message": f"User profile '{u_clean}' not found. Register a new profile or log in as Admin."}

def register_new_profile(username: str, password: str) -> dict:
    """Registers a new personal profile on Aria."""
    u_clean = username.strip()
    p_clean = password.strip()
    if not u_clean or not p_clean:
        return {"success": False, "message": "Username and password required."}
    if u_clean.lower() == "l":
        return {"success": False, "message": "Username 'L' is reserved for Master Admin."}
        
    store = _load_auth_store()
    if u_clean in store.get("users", {}):
        return {"success": False, "message": f"Profile '{u_clean}' already exists."}
        
    store.setdefault("users", {})[u_clean] = {
        "password_hash": _hash_pass(p_clean),
        "role": "user",
        "display_name": u_clean,
        "is_master": False,
        "created": time.strftime("%Y-%m-%d")
    }
    _save_auth_store(store)
    return {"success": True, "message": f"Profile '{u_clean}' created successfully! You can now log in."}

def verify_session(token: str) -> dict:
    """Validates an active session token."""
    if not token:
        return {"authenticated": False, "role": "guest", "is_admin": False, "username": "Guest"}
    if token.startswith("admin_") and token in _ACTIVE_SESSIONS:
        sess = _ACTIVE_SESSIONS[token]
        return {"authenticated": True, "role": "admin", "is_admin": True, "username": sess.get("username", "L")}
    if token in _ACTIVE_SESSIONS:
        sess = _ACTIVE_SESSIONS[token]
        return {"authenticated": True, "role": sess.get("role", "user"), "is_admin": sess.get("is_admin", False), "username": sess.get("username", "User")}
    return {"authenticated": False, "role": "guest", "is_admin": False, "username": "Guest"}

def _get_host_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_devices_status() -> dict:
    """Returns connected devices and host laptop status."""
    store = _load_auth_store()
    return {
        "master_device": {
            "name": f"Host Laptop ({socket.gethostname()})",
            "status": "Online / Master Host",
            "ip": _get_host_ip(),
            "admin": MASTER_ADMIN_USER
        },
        "registered_profiles": list(store.get("users", {}).keys()),
        "active_sessions_count": len(_ACTIVE_SESSIONS)
    }
