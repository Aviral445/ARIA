"""
Aria Smart Bulb Controller (Tuya / DigiTap local Wi-Fi protocol)
Direct LAN control via AES-encrypted Tuya 3.5 protocol without cloud latency.
"""
import os
import json
import socket
from pathlib import Path

BULB_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "smart_bulb.json")

def load_bulb_config() -> dict:
    if os.path.exists(BULB_CONFIG_FILE):
        try:
            with open(BULB_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "name": "room bulb",
        "ip": "192.168.1.8",
        "id": "d7721a192df87054a3ivut",
        "local_key": "",
        "version": 3.5,
        "product_key": "key8u54q9dtru5jw"
    }

def save_bulb_config(cfg: dict):
    os.makedirs(os.path.dirname(BULB_CONFIG_FILE), exist_ok=True)
    with open(BULB_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def auto_discover_bulb(timeout: int = 3) -> dict | None:
    """Scans local subnet for Tuya protocol broadcast packets to auto-update bulb IP."""
    try:
        import tinytuya
        devices = tinytuya.deviceScan(False, timeout)
        cfg = load_bulb_config()
        target_id = cfg.get("id", "d7721a192df87054a3ivut")
        for dev_ip, dev_info in devices.items():
            if dev_info.get("gwId") == target_id or dev_info.get("id") == target_id:
                cfg["ip"] = dev_ip
                if "version" in dev_info:
                    try:
                        cfg["version"] = float(dev_info["version"])
                    except Exception:
                        pass
                save_bulb_config(cfg)
                return cfg
    except Exception as e:
        print(f"Bulb discovery error: {e}")
    return None

def control_bulb(action: str, **kwargs) -> tuple[bool, str]:
    """
    Controls the local Tuya bulb.
    action: 'on', 'off', 'toggle', 'status'
    """
    try:
        import tinytuya
    except ImportError:
        return False, "tinytuya library is not installed."

    cfg = load_bulb_config()
    dev_id = cfg.get("id", "d7721a192df87054a3ivut")
    ip = cfg.get("ip", "192.168.1.8")
    local_key = cfg.get("local_key", "").strip()
    version = cfg.get("version", 3.5)

    if not local_key:
        return False, (
            f"Found your bulb at {ip} (Device ID: {dev_id}), but the 16-character Local Key is missing in config/smart_bulb.json. "
            "Please provide your Tuya/DigiTap Local Key so I can send encrypted commands."
        )

    action = action.lower().strip()

    try:
        d = tinytuya.BulbDevice(dev_id, ip, local_key)
        d.set_version(version)
        d.set_socketPersistent(False)

        if action in ["on", "turn on", "switch on"]:
            res = d.turn_on()
            if isinstance(res, dict) and "Error" in res:
                # Try re-discovering in case IP changed
                new_cfg = auto_discover_bulb()
                if new_cfg and new_cfg.get("ip") != ip:
                    d = tinytuya.BulbDevice(dev_id, new_cfg["ip"], local_key)
                    d.set_version(version)
                    res = d.turn_on()
                if isinstance(res, dict) and "Error" in res:
                    return False, f"Failed to turn on bulb: {res.get('Error')}"
            return True, f"Turned ON the {cfg.get('name', 'bulb')}."

        elif action in ["off", "turn off", "switch off"]:
            res = d.turn_off()
            if isinstance(res, dict) and "Error" in res:
                new_cfg = auto_discover_bulb()
                if new_cfg and new_cfg.get("ip") != ip:
                    d = tinytuya.BulbDevice(dev_id, new_cfg["ip"], local_key)
                    d.set_version(version)
                    res = d.turn_off()
                if isinstance(res, dict) and "Error" in res:
                    return False, f"Failed to turn off bulb: {res.get('Error')}"
            return True, f"Turned OFF the {cfg.get('name', 'bulb')}."

        elif action in ["toggle"]:
            status = d.status()
            if isinstance(status, dict) and "dps" in status:
                is_on = status["dps"].get("20", status["dps"].get("1", False))
                if is_on:
                    d.turn_off()
                    return True, f"Turned OFF the {cfg.get('name', 'bulb')}."
                else:
                    d.turn_on()
                    return True, f"Turned ON the {cfg.get('name', 'bulb')}."
            else:
                # Fallback: try turning on
                d.turn_on()
                return True, f"Toggled {cfg.get('name', 'bulb')}."

        elif action == "status":
            st = d.status()
            return True, f"Bulb status: {json.dumps(st)}"

        return False, f"Unknown bulb action: {action}"

    except Exception as e:
        return False, f"Bulb connection error: {e}"
