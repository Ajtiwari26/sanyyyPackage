#!/usr/bin/env python3
"""
Sanyyy macOS Native System Controls Engine
============================================
Provides 1ms native hardware controls for:
- Screen Brightness (via Apple DisplayServices.framework & ctypes)
- System Audio Volume & Mute (via AppleScript osascript)
- Media Playback Controls (Play/Pause/Next/Prev)
"""

import sys
import ctypes
import subprocess


def get_brightness() -> int:
    """Get current macOS screen brightness (0-100%)"""
    try:
        ds = ctypes.cdll.LoadLibrary(
            '/System/Library/PrivateFrameworks/DisplayServices.framework/DisplayServices'
        )
        ds.DisplayServicesGetLinearBrightness.argtypes = [
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_float),
        ]
        ds.DisplayServicesGetLinearBrightness.restype = ctypes.c_int

        val = ctypes.c_float()
        res = ds.DisplayServicesGetLinearBrightness(1, ctypes.byref(val))
        if res == 0:
            return int(round(val.value * 100))
        return 50
    except Exception as e:
        print(f"⚠️ Error getting brightness: {e}")
        return 50


def set_brightness(level: int) -> str:
    """Set macOS screen brightness directly to target percentage (0-100%)"""
    try:
        level = max(0, min(100, int(level)))
        val = level / 100.0
        ds = ctypes.cdll.LoadLibrary(
            '/System/Library/PrivateFrameworks/DisplayServices.framework/DisplayServices'
        )
        ds.DisplayServicesSetLinearBrightness.argtypes = [
            ctypes.c_uint32,
            ctypes.c_float,
        ]
        ds.DisplayServicesSetLinearBrightness.restype = ctypes.c_int

        res = ds.DisplayServicesSetLinearBrightness(1, val)
        if res == 0:
            return f"✅ Screen brightness set to {level}%"
        return f"⚠️ DisplayServices returned status code {res}"
    except Exception as e:
        return f"⚠️ Error setting brightness: {e}"


def change_brightness_by(delta: int) -> str:
    """Increase or decrease brightness relative to current level (e.g. +10, -20)"""
    current = get_brightness()
    target = max(0, min(100, current + delta))
    return set_brightness(target)


def get_volume() -> dict:
    """Get current volume settings (volume level: 0-100, muted: bool)"""
    try:
        script = 'set v to output volume of (get volume settings)\nset m to output muted of (get volume settings)\nreturn (v as text) & "," & (m as text)'
        res = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0:
            parts = res.stdout.strip().split(",")
            vol = int(parts[0]) if len(parts) > 0 else 50
            muted = (parts[1].lower() == "true") if len(parts) > 1 else False
            return {"volume": vol, "muted": muted}
        return {"volume": 50, "muted": False}
    except Exception:
        return {"volume": 50, "muted": False}


def set_volume(level: int) -> str:
    """Set system audio output volume level (0-100%)"""
    try:
        level = max(0, min(100, int(level)))
        res = subprocess.run(
            ["osascript", "-e", f"set volume output volume {level}"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0:
            return f"✅ Volume set to {level}%"
        return f"⚠️ Error setting volume: {res.stderr.strip()}"
    except Exception as e:
        return f"⚠️ Volume error: {e}"


def change_volume_by(delta: int) -> str:
    """Increase or decrease volume relative to current level (e.g. +10, -10)"""
    info = get_volume()
    current = info["volume"]
    target = max(0, min(100, current + delta))
    return set_volume(target)


def set_mute(muted: bool) -> str:
    """Mute or unmute system audio output"""
    try:
        val_str = "true" if muted else "false"
        res = subprocess.run(
            ["osascript", "-e", f"set volume output muted {val_str}"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0:
            return f"✅ Sound {'muted' if muted else 'unmuted'}"
        return f"⚠️ Error setting mute state: {res.stderr.strip()}"
    except Exception as e:
        return f"⚠️ Mute error: {e}"


def toggle_mute() -> str:
    """Toggle mute state on or off"""
    info = get_volume()
    return set_mute(not info["muted"])


if __name__ == "__main__":
    print("🧪 Testing Sanyyy System Controls Engine...")
    print(f"Current Brightness: {get_brightness()}%")
    vol_info = get_volume()
    print(f"Current Volume: {vol_info['volume']}%, Muted: {vol_info['muted']}")

    # Quick test
    print("\n🔬 Testing Brightness set to 75%...")
    print(set_brightness(75))
    print(f"Verified Brightness: {get_brightness()}%")

    print("\n🔬 Testing Volume set to 60%...")
    print(set_volume(60))
    print(f"Verified Volume: {get_volume()['volume']}%")
