#!/usr/bin/env python3
"""
Sanyyy Layered Memory & Preference Store
==========================================
Manages persistent user preferences and task history using fast, append-only JSONL files.

Storage Locations:
- ~/.sanyyy/preferences.jsonl  (User preferences: preferred browser, Chrome profiles, editors, habits)
- ~/.sanyyy/task_history.jsonl (Episodic memory: goal, steps taken, success, duration)
"""

import os
import json
import time
from datetime import datetime, timezone

MEMORY_DIR = os.path.expanduser("~/.sanyyy")
PREFERENCES_FILE = os.path.join(MEMORY_DIR, "preferences.jsonl")
HISTORY_FILE = os.path.join(MEMORY_DIR, "task_history.jsonl")

def ensure_memory_dir():
    """Ensure ~/.sanyyy directory exists"""
    os.makedirs(MEMORY_DIR, exist_ok=True)

def save_preference(key: str, value: str, context: str = "") -> dict:
    """
    Save or update a user preference entry in preferences.jsonl.
    Append-only log — latest key entry overrides earlier entries when read.
    """
    ensure_memory_dir()
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "key": key.lower().strip(),
        "value": str(value).strip(),
        "context": context.strip()
    }
    with open(PREFERENCES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"🧠 Memory Saved: {key} = '{value}' ({context})")
    return record

def get_all_preferences() -> dict:
    """
    Read preferences.jsonl and return dict of latest values for each key.
    """
    ensure_memory_dir()
    if not os.path.exists(PREFERENCES_FILE):
        return {}

    prefs = {}
    with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                k = data.get("key")
                v = data.get("value")
                if k and v:
                    prefs[k] = v
            except Exception:
                continue
    return prefs

def get_preference(key: str, default: str = None) -> str:
    """Get the latest stored preference for key"""
    prefs = get_all_preferences()
    return prefs.get(key.lower().strip(), default)

def record_task_execution(goal: str, steps_completed: int, total_steps: int, success: bool, duration_s: float, notes: str = "") -> dict:
    """Record completed or attempted task execution in task_history.jsonl"""
    ensure_memory_dir()
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal.strip(),
        "steps_completed": steps_completed,
        "total_steps": total_steps,
        "success": success,
        "duration_s": round(duration_s, 2),
        "notes": notes.strip()
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"📜 Task History Recorded: '{goal}' | Success={success} ({duration_s:.1f}s)")
    return record

def get_formatted_preferences_context() -> str:
    """Format preferences as clean context string for LLM prompts"""
    prefs = get_all_preferences()
    if not prefs:
        return "User Preferences: None saved yet."
    lines = ["Stored User Preferences (JSONL Memory):"]
    for k, v in prefs.items():
        lines.append(f"  • {k}: {v}")
    return "\n".join(lines)

if __name__ == "__main__":
    print("🧪 Testing Sanyyy Memory & Preference Store...")
    save_preference("preferred_browser", "Google Chrome", "web automation tasks")
    save_preference("gcp_profile", "Coursewaalah", "Google Cloud account tasks")
    print(get_formatted_preferences_context())
