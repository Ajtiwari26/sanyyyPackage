"""
🌸 SANYYY CONFIG & HARDWARE IDENTIFIER MANAGER
Handles local configuration storage (%APPDATA%\Sanyyy\config.json)
and generates unique hardware IDs for device locking.
"""

import os
import sys
import json
import uuid
import platform
import subprocess

# Config storage directory
if platform.system() == "Windows":
    CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Sanyyy")
else:
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".sanyyy")

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def get_hardware_id():
    """Generates unique Hardware Identifier (HWID) bound to motherboard / CPU."""
    try:
        if platform.system() == "Windows":
            cmd = "wmic csproduct get uuid"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
            lines = [line.strip() for line in output.split("\n") if line.strip()]
            if len(lines) > 1:
                return lines[1]
        elif platform.system() == "Darwin":
            cmd = "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if output:
                return output
    except Exception:
        pass
    
    # Fallback to MAC address node string
    return f"HWID-{hex(uuid.getnode()).upper()}"

def load_config():
    """Loads configuration dictionary from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error loading config: {e}")
    return {}

def save_config(data):
    """Saves configuration dictionary to file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[+] Configuration saved to: {CONFIG_FILE}")

def get_backend_url():
    """Returns license backend API URL (Defaults to live Vercel backend: https://backend-teal-chi-51.vercel.app)."""
    cfg = load_config()
    return cfg.get("backend_url", "https://backend-teal-chi-51.vercel.app")
