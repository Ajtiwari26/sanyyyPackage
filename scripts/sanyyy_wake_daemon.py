#!/usr/bin/env python3
"""
Sanyyy Native macOS Wake Daemon
================================
Uses Apple's native NSSpeechRecognizer framework for 100% offline,
instant, 0-token wake word detection on macOS.

Architecture:
  IDLE MODE (0 tokens) → Apple NSSpeechRecognizer listens natively in background
  ACTIVE MODE (Gemini tokens) → launches gemini_live_agent.py as subprocess
  "Go to sleep" → subprocess exits → back to IDLE MODE (0 tokens)
"""

import os
import sys
import time
import signal
import subprocess
from AppKit import NSObject, NSSpeechRecognizer
from Foundation import NSRunLoop, NSDate, NSTimer

# ── Configuration ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_SCRIPT = os.path.join(SCRIPT_DIR, "gemini_live_agent.py")
PYTHON_BIN = "/opt/homebrew/bin/python3"

# Native commands to register with Apple's Speech Recognizer
WAKE_COMMANDS = [
    "wakeup sanyyy",
    "wake up sanyyy",
    "hey sanyyy",
    "hi sanyyy",
    "sanyyy wake up",
    "sanyyy",
    "wakeup",
    "wake up",
    "breakup saini",
    "saini",
]

wake_triggered = False

class SanyyySpeechDelegate(NSObject):
    """Apple NSSpeechRecognizer Delegate"""
    def speechRecognizer_didRecognizeCommand_(self, sender, command):
        global wake_triggered
        cmd_str = str(command).strip()
        print(f"\n\n🌟 NATIVE WAKE WORD DETECTED: '{cmd_str}'")
        wake_triggered = True


def launch_sanyyy():
    """
    ACTIVE MODE: Launch gemini_live_agent.py as a subprocess.
    Waits for it to exit (user said "go to sleep").
    Returns exit code.
    """
    print("\n🌸 Waking up Sanyyy Voice + Vision Engine...\n")
    print("=" * 50)

    try:
        process = subprocess.Popen(
            [PYTHON_BIN, AGENT_SCRIPT],
            cwd=SCRIPT_DIR,
        )
        # Wait for agent process to finish (user said "go to sleep" or exit)
        exit_code = process.wait()
        print(f"\n💤 Sanyyy went to sleep (exit code: {exit_code})")
        return exit_code
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        print("\n👋 Sanyyy terminated by user.")
        return 0
    except Exception as e:
        print(f"\n⚠️ Error launching Sanyyy: {e}")
        return 1


def main():
    global wake_triggered
    print("🌙 Sanyyy Native macOS Wake-Word Daemon Starting...")
    print("=" * 50)
    print("🔑 Account: Coursewaalah Private Limited")
    print("🎙️ Voice: Aoede (Female)")
    print("👂 Engine: Apple Native NSSpeechRecognizer (100% Offline, 0 Tokens)")
    print("🛑 Sleep Command: 'Go to sleep' / 'Soja Sanyyy'")
    print("=" * 50)

    # Initialize Apple Native Speech Recognizer
    try:
        recognizer = NSSpeechRecognizer.alloc().init()
        delegate = SanyyySpeechDelegate.alloc().init()
        recognizer.setDelegate_(delegate)
        recognizer.setCommands_(WAKE_COMMANDS)
        recognizer.setListensInForegroundOnly_(False)
        print(f"✅ Registered native commands: {list(recognizer.commands())}")
    except Exception as err:
        print(f"❌ Failed to initialize NSSpeechRecognizer: {err}")
        sys.exit(1)

    # Register clean signal handlers
    def shutdown_handler(sig, frame):
        print(f"\n👋 Wake daemon received signal {sig} — shutting down cleanly.")
        try:
            recognizer.stopListening()
        except Exception:
            pass
        sys.exit(0)

    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, shutdown_handler)
        except Exception:
            pass

    print("\n💤 Sanyyy is sleeping... Say 'Wakeup Sanyyy' or 'Hey Sanyyy' to activate!\n")
    recognizer.startListening()

    # Main RunLoop for native Apple event dispatch
    while True:
        try:
            # Run NSRunLoop in 0.5s ticks to process Apple speech events
            NSRunLoop.currentRunLoop().runUntilDate_(
                NSDate.dateWithTimeIntervalSinceNow_(0.5)
            )

            if wake_triggered:
                wake_triggered = False
                # Pause native speech recognizer while Gemini agent is running
                recognizer.stopListening()

                # Launch Sanyyy Gemini Live agent
                launch_sanyyy()

                # Agent finished ("go to sleep") — resume native wake-word listening
                print("\n⏳ Returning to native idle wake-word listening...\n")
                time.sleep(1.5)
                print("💤 Sanyyy is sleeping... Say 'Wakeup Sanyyy' to activate!\n")
                recognizer.startListening()

        except KeyboardInterrupt:
            print("\n👋 Sanyyy Wake Daemon shutdown complete.")
            recognizer.stopListening()
            break
        except Exception as e:
            print(f"⚠️ RunLoop error: {e}")
            time.sleep(1.0)


if __name__ == "__main__":
    main()
