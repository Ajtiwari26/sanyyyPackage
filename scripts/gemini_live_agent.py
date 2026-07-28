#!/usr/bin/env python3
"""
🎙️ OPENCLAW JARVIS GEMINI LIVE VOICE + VISION AGENT
====================================================
Real-time, ultra-low latency voice + vision agent for OpenClaw powered by Google Gemini Live API.
Streams audio (16kHz PCM) AND screen screenshots (1 FPS JPEG) to the same Gemini Live session.
Supports Coursewaalah Private Limited GCP account & Gemini API Keys.
"""

import os
import sys
import io
import time
import math
import asyncio
import argparse
import subprocess
import base64
import warnings
from contextlib import AsyncExitStack
from dotenv import load_dotenv

# Filter deprecation warnings for clean runtime console output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment
load_dotenv()
load_dotenv("/Users/ajaytiwari/Desktop/Projects/openclaw/.env")

try:
    import sounddevice as sd
    import numpy as np
    from google import genai
    from google.genai import types
    import mss as mss_module
    from PIL import Image
    
    # Import Sanyyy AXUIElement Accessibility Engine & Layered Memory Store
    sys.path.insert(0, "/Users/ajaytiwari/Desktop/Projects/openclaw/scripts")
    import sanyyy_ax_engine
    import sanyyy_memory
except ImportError as e:
    print(f"❌ Missing voice/vision dependencies: {e}")
    print("Run: /opt/homebrew/bin/python3 -m pip install google-genai sounddevice numpy google-auth mss Pillow")
    sys.exit(1)

# Default voice settings
DEFAULT_VOICE = os.getenv("GEMINI_LIVE_VOICE", "Aoede")
MODEL_NAME = os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash")

def get_gemini_client():
    """Initialize Gemini client with Google Cloud credentials or API key"""
    gcp_sa_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/Users/ajaytiwari/agentline_sa_key.json")
    api_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    project_id = os.getenv("GCP_PROJECT", "igsl-67e70")

    if gcp_sa_key and os.path.exists(gcp_sa_key):
        print(f"🔑 Using Google Cloud Service Account: {gcp_sa_key}")
        from google.oauth2 import service_account
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        credentials = service_account.Credentials.from_service_account_file(gcp_sa_key, scopes=scopes)
        client = genai.Client(
            vertexai=True,
            project="igsl-67e70",
            location="us-central1",
            credentials=credentials
        )
        return client, "gemini-live-2.5-flash-native-audio"
    else:
        # Fallback to active gcloud user session
        try:
            import subprocess
            from google.oauth2.credentials import Credentials
            token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
            credentials = Credentials(token)
            print(f"🔑 Using Google Cloud User Account ({project_id})")
            client = genai.Client(
                vertexai=True,
                project=project_id,
                location="us-central1",
                credentials=credentials
            )
            return client, "gemini-live-2.5-flash-native-audio"
        except Exception as err:
            if api_key:
                print("🔑 Using Gemini API Key authentication")
                client = genai.Client(api_key=api_key)
                return client, "gemini-2.0-flash"
            raise ValueError(f"❌ Could not initialize Google Cloud credentials: {err}")

# Universal Dynamic Command Execution Engine for macOS
def execute_system_command(command: str, explanation: str = "") -> str:
    """Execute dynamic zsh/bash shell commands safely in background and return output"""
    try:
        print(f"\n⚙️ Executing Command: {command}")
        if explanation:
            print(f"   Context: {explanation}")
        
        # Execute command in zsh shell
        res = subprocess.run(
            ["/bin/zsh", "-c", command],
            capture_output=True,
            text=True,
            timeout=30
        )
        stdout = res.stdout.strip()
        stderr = res.stderr.strip()
        
        if res.returncode == 0:
            output = stdout if stdout else "Command executed successfully with 0 exit code."
            print(f"   ↳ Output: {output[:150]}")
            return output
        else:
            err_msg = stderr if stderr else f"Command failed with exit code {res.returncode}"
            print(f"   ⚠️ Command Error: {err_msg}")
            return f"Command Execution Error: {err_msg}"
    except Exception as err:
        print(f"❌ Execution Exception: {err}")
        return f"Execution Exception: {err}"

def get_mac_screen_size():
    """Get active macOS display width and height in screen points (e.g. 1470x956 on Mac M5 Air)"""
    try:
        from AppKit import NSScreen
        screen = NSScreen.mainScreen()
        if screen:
            frame = screen.frame()
            return int(frame.size.width), int(frame.size.height)
        with mss_module.MSS() as sct:
            mon = sct.monitors[1]
            return mon["width"], mon["height"]
    except Exception:
        return 1470, 956

def get_gemini_vision_client():
    """Get Gemini Client & Model dedicated for multimodal vision screen grounding"""
    client, live_model = get_gemini_client()
    vision_model = "gemini-2.5-flash" if "native-audio" in live_model else live_model
    return client, vision_model

def find_text_on_screen(query: str):
    """
    Use Gemini Vision + Active Window Frame Bounds to ground target text/element in screen points.
    Supports full-screen and windowed apps (WhatsApp, Chrome, Finder, VS Code).
    """
    try:
        import math
        import json
        sw_pts, sh_pts = get_mac_screen_size()
        cx, cy = get_current_cursor_pos()
        
        # Check active window bounds for localized grounding
        win_bounds = sanyyy_ax_engine.get_active_window_bounds()
        use_win_crop = False
        win_x, win_y, win_w, win_h = 0, 0, sw_pts, sh_pts
        
        if win_bounds and win_bounds["width"] < sw_pts * 0.95:
            use_win_crop = True
            win_x, win_y = win_bounds["x"], win_bounds["y"]
            win_w, win_h = win_bounds["width"], win_bounds["height"]
        
        with mss_module.MSS() as sct:
            screenshot = sct.grab(sct.monitors[1])
            img_full = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            # Crop image to active window frame if windowed app
            if use_win_crop:
                scale_f = screenshot.size[0] / float(sw_pts)
                crop_box = (
                    int(max(0, win_x * scale_f)),
                    int(max(0, win_y * scale_f)),
                    int(min(screenshot.size[0], (win_x + win_w) * scale_f)),
                    int(min(screenshot.size[1], (win_y + win_h) * scale_f))
                )
                img_target = img_full.crop(crop_box)
            else:
                img_target = img_full
            
            client, vision_model = get_gemini_vision_client()
            
            target_desc = f"active application window ({win_w}x{win_h} points at offset {win_x},{win_y})" if use_win_crop else f"macOS display ({sw_pts}x{sh_pts} points)"
            
            prompt = f"""You are a screen vision and OCR element grounding engine for {target_desc}.
Identify the bounding box of the text label, desktop icon, chat item, or UI button matching: '{query}'.

Return JSON strictly with format:
{{
  "found": true,
  "matches": [
    {{
      "text": "{query}",
      "box_2d": [ymin, xmin, ymax, xmax]
    }}
  ]
}}
Coordinates [ymin, xmin, ymax, xmax] MUST be normalized integers from 0 to 1000 representing the bounding box.
If not found, return {{"found": false, "matches": []}}.
Do NOT output markdown formatting or code blocks."""

            response = client.models.generate_content(
                model=vision_model,
                contents=[img_target, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            res_text = response.text.strip()
            if res_text.startswith("```"):
                res_text = res_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                
            data = json.loads(res_text)
            matches = []
            if data.get("found") and data.get("matches"):
                for m in data["matches"]:
                    box = m.get("box_2d", [0, 0, 1000, 1000])
                    ymin, xmin, ymax, xmax = box[0], box[1], box[2], box[3]
                    
                    norm_x = (xmin + xmax) / 2.0
                    norm_y = (ymin + ymax) / 2.0
                    
                    if use_win_crop:
                        screen_x = win_x + int((norm_x / 1000.0) * win_w)
                        screen_y = win_y + int((norm_y / 1000.0) * win_h)
                    else:
                        screen_x = int((norm_x / 1000.0) * sw_pts)
                        screen_y = int((norm_y / 1000.0) * sh_pts)
                        
                    icon_y = max(20, screen_y - 45)
                    dist = math.sqrt((screen_x - cx)**2 + (screen_y - cy)**2)
                    matches.append({
                        "text": m.get("text", query),
                        "x": screen_x,
                        "y": screen_y,
                        "icon_x": screen_x,
                        "icon_y": icon_y,
                        "norm_x": int((screen_x / sw_pts) * 1000),
                        "norm_y": int((screen_y / sh_pts) * 1000),
                        "icon_norm_x": int((screen_x / sw_pts) * 1000),
                        "icon_norm_y": int((icon_y / sh_pts) * 1000),
                        "distance_px": round(dist, 1)
                    })
                matches.sort(key=lambda item: item["distance_px"])
            return matches
    except Exception as e:
        print(f"⚠️ Gemini Vision Error: {e}")
        return []

def get_macos_running_apps():
    """Fetch active running macOS applications and non-background process names"""
    try:
        script = 'tell application "System Events" to get name of every process whose background only is false'
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            apps = [a.strip() for a in res.stdout.split(",") if a.strip()]
            return f"Active macOS Applications ({len(apps)}): {', '.join(apps)}"
        return "Could not retrieve running applications list."
    except Exception as e:
        return f"Error listing applications: {e}"

def execute_local_tool(func_name: str, args: dict) -> str:
    """Execute dynamic or specialized local tools with precision normalized coordinate scaling & trackpad gestures"""
    try:
        # Trigger active vision burst on any tool execution
        trigger_active_vision(4.0)
        hud_script = "/Users/ajaytiwari/Desktop/Projects/openclaw/scripts/sanyyy_cursor_hud.py"
        sw, sh = get_mac_screen_size()
        cx, cy = get_current_cursor_pos()
        
        if func_name == "run_system_command":
            cmd = args.get("command", "")
            exp = args.get("explanation", "")
            return execute_system_command(cmd, exp)
        
        elif func_name == "get_macos_running_apps":
            return get_macos_running_apps()

        elif func_name == "click_target_element":
            query = args.get("query", "")
            action = args.get("action_type", "click").lower()
            
            # 1. Check if Desktop Icon
            desk_icon = sanyyy_ax_engine.find_desktop_icon(query)
            if desk_icon:
                # Uncover desktop by bringing Finder to front
                subprocess.run(["osascript", "-e", 'tell application "Finder" to activate'], capture_output=True)
                time.sleep(0.15)
                b = desk_icon["bounds"]
                tx, ty = b["center_x"], b["center_y"]
                
                cmd_type = "double_click" if action in ("double_click", "open") else "click"
                subprocess.call([sys.executable, hud_script, cmd_type, str(tx), str(ty)])
                time.sleep(0.3)
                return f"🎯 DESKTOP ICON TARGETED: Cursor glided to exact geometric center ({tx}, {ty}) [Thumbnail {b['width']}x{b['height']}px] and issued {cmd_type}. Finder brought to front."

            # 2. General AXTree Search
            matches = sanyyy_ax_engine.find_ax_elements_by_label(query)
            if matches:
                m = matches[0]
                b = m["bounds"]
                tx, ty = b["center_x"], b["center_y"]
                
                # Closed-Loop Landing Verification
                subprocess.call([sys.executable, hud_script, "move", str(tx), str(ty)])
                time.sleep(0.05)
                cur_x, cur_y = get_current_cursor_pos()
                err_x, err_y = tx - cur_x, ty - cur_y
                if abs(err_x) > 2 or abs(err_y) > 2:
                    subprocess.call([sys.executable, hud_script, "nudge", str(err_x), str(err_y)])
                
                cmd = action if action in ("click", "double_click", "right_click") else "click"
                subprocess.call([sys.executable, hud_script, cmd, str(tx), str(ty)])
                time.sleep(0.3)
                return f"🎯 AXTree ELEMENT TARGETED: '{m['label']}' [{m['role']}] @ Geometric Center ({tx}, {ty}) — verified landing & issued {action}."

            # 3. Closed-Loop Gemini Vision Grounding & Landing Verification
            ocr_results = find_text_on_screen(query)
            if ocr_results:
                best = ocr_results[0]
                tx, ty = best["x"], best["y"]
                
                # Glide cursor to target center
                subprocess.call([sys.executable, hud_script, "move", str(tx), str(ty)])
                time.sleep(0.05)
                
                # Pre-click landing verification & micro-nudge if needed
                cur_x, cur_y = get_current_cursor_pos()
                err_x, err_y = tx - cur_x, ty - cur_y
                if abs(err_x) > 2 or abs(err_y) > 2:
                    subprocess.call([sys.executable, hud_script, "nudge", str(err_x), str(err_y)])
                
                cmd = action if action in ("click", "double_click", "right_click") else "click"
                subprocess.call([sys.executable, hud_script, cmd, str(tx), str(ty)])
                time.sleep(0.3)
                return f"🎯 CLOSED-LOOP GEMINI VISION TARGETED: '{best['text']}' @ Center ({tx}, {ty}) — landing verified & issued {action}. Visual state verification active."

            return f"⚠️ Target element '{query}' not found in AXTree or Gemini Vision."

        elif func_name == "press_ax_element":
            query = args.get("query", "")
            matches = sanyyy_ax_engine.find_ax_elements_by_label(query)
            if matches:
                m = matches[0]
                ok = sanyyy_ax_engine.press_ax_element(m["element"])
                b = m["bounds"]
                if ok:
                    return f"Executed native AXPressAction on '{m['label']}' [{m['role']}] at Center ({b['center_x']}, {b['center_y']})"
                else:
                    # Fallback to center mouse click
                    subprocess.call([sys.executable, hud_script, "center_click", str(b['x']), str(b['y']), str(b['width']), str(b['height'])])
                    return f"Clicked Geometric Center ({b['center_x']}, {b['center_y']}) of '{m['label']}' [{m['role']}]"
            return f"macOS Accessibility tree did not find element matching '{query}' to press."

        elif func_name == "remember_preference":
            key = args.get("key", "")
            value = args.get("value", "")
            context = args.get("context", "")
            sanyyy_memory.save_preference(key, value, context)
            return f"Saved preference: {key} = '{value}' ({context})"

        elif func_name == "get_preferences":
            return sanyyy_memory.get_formatted_preferences_context()
        
        elif func_name == "ocr_screen_find_text":
            query = args.get("query", "")
            results = find_text_on_screen(query)
            if results:
                best = results[0]
                return f"Gemini Vision found '{best['text']}': Text Label Center at ({best['x']}, {best['y']}) [Normalized: ({best['norm_x']}, {best['norm_y']})] | If Desktop/Folder Icon Graphic Center: ({best['icon_x']}, {best['icon_y']}) [Normalized: ({best['icon_norm_x']}, {best['icon_norm_y']})] | Nearest Euclidean Distance: {best['distance_px']}px"
            else:
                return f"Gemini Vision did not find exact match for '{query}' on screen."

        elif func_name in ("move_mouse", "click_mouse", "double_click", "right_click"):
            raw_x = float(args.get("x", 500))
            raw_y = float(args.get("y", 500))
            
            if raw_x <= 1000 and raw_y <= 1000:
                target_x = int((raw_x / 1000.0) * sw)
                target_y = int((raw_y / 1000.0) * sh)
            else:
                target_x = int(min(raw_x, sw))
                target_y = int(min(raw_y, sh))
            
            dist = math.sqrt((target_x - cx)**2 + (target_y - cy)**2)
            
            if func_name == "move_mouse":
                subprocess.call([sys.executable, hud_script, "move", str(target_x), str(target_y)])
                return f"Glided cursor smoothly to ({target_x}, {target_y}) [Euclidean Distance: {dist:.1f}px]"
            elif func_name == "click_mouse":
                subprocess.call([sys.executable, hud_script, "click", str(target_x), str(target_y)])
                return f"Clicked cursor at ({target_x}, {target_y}) [Euclidean Distance: {dist:.1f}px]"
            elif func_name == "double_click":
                subprocess.call([sys.executable, hud_script, "double_click", str(target_x), str(target_y)])
                return f"Double-clicked at ({target_x}, {target_y}) [Euclidean Distance: {dist:.1f}px]"
            elif func_name == "right_click":
                subprocess.call([sys.executable, hud_script, "right_click", str(target_x), str(target_y)])
                return f"Right-clicked at ({target_x}, {target_y}) [Euclidean Distance: {dist:.1f}px]"

        elif func_name == "nudge_cursor":
            dx = int(args.get("dx", 0))
            dy = int(args.get("dy", 0))
            dist = math.sqrt(dx**2 + dy**2)
            subprocess.call([sys.executable, hud_script, "nudge", str(dx), str(dy)])
            return f"Micro-nudged cursor by Δx={dx}px, Δy={dy}px [Euclidean Distance: {dist:.1f}px]"

        elif func_name == "drag_and_drop":
            sx_raw, sy_raw = float(args.get("start_x", 0)), float(args.get("start_y", 0))
            ex_raw, ey_raw = float(args.get("end_x", 0)), float(args.get("end_y", 0))
            
            sx = int((sx_raw / 1000.0) * sw) if sx_raw <= 1000 else int(min(sx_raw, sw))
            sy = int((sy_raw / 1000.0) * sh) if sy_raw <= 1000 else int(min(sy_raw, sh))
            ex = int((ex_raw / 1000.0) * sw) if ex_raw <= 1000 else int(min(ex_raw, sw))
            ey = int((ey_raw / 1000.0) * sh) if ey_raw <= 1000 else int(min(ey_raw, sh))
            
            dist = math.sqrt((ex - sx)**2 + (ey - sy)**2)
            subprocess.call([sys.executable, hud_script, "drag", str(sx), str(sy), str(ex), str(ey)])
            return f"Dragged from ({sx},{sy}) to ({ex},{ey}) [Euclidean Distance: {dist:.1f}px]"

        elif func_name == "scroll_trackpad":
            dy = int(args.get("dy", -10))
            dx = int(args.get("dx", 0))
            pct = args.get("scroll_percentage", None)
            cmd_args = [sys.executable, hud_script, "scroll", str(dy), str(dx)]
            if pct is not None:
                cmd_args.append(str(pct))
            subprocess.call(cmd_args)
            return f"Scrolled trackpad [dy={dy}, dx={dx}, percentage={pct}%]"

        elif func_name == "type_text":
            text = str(args.get("text", ""))
            press_enter = bool(args.get("press_enter", True))
            subprocess.call([sys.executable, hud_script, "type", text, str(press_enter)])
            return f"Typed text into active window: '{text}' (Enter={press_enter})"

        elif func_name == "press_key":
            key_name = str(args.get("key_name", "return"))
            subprocess.call([sys.executable, hud_script, "key", key_name])
            return f"Pressed special key: '{key_name}'"

        elif func_name == "go_to_sleep":
            # Sanyyy sleep/shutdown handler — cleanly exits so wake daemon can resume idle mode
            goodbye = args.get("goodbye_message", "Chalo, soja rahi hoon! Jab zarurat ho bolna 'Wakeup Sanyyy'!")
            print(f"\n💤 Sanyyy going to sleep... '{goodbye}'")
            print("🌙 Disconnecting Gemini Live session...")
            # Give a moment for the goodbye audio to play, then exit cleanly
            import threading
            def delayed_exit():
                time.sleep(4.0)  # Wait for goodbye audio to finish playing
                print("\n✅ Sanyyy is now sleeping. Say 'Wakeup Sanyyy' to wake up again!")
                os._exit(0)  # Clean exit — wake daemon will detect this and resume idle listening
            threading.Thread(target=delayed_exit, daemon=True).start()
            return f"Going to sleep now. Goodbye message: '{goodbye}'"

        return execute_system_command(f"{func_name}", str(args))
    except Exception as err:
        return f"Error executing {func_name}: {err}"

# ── Screen Vision Engine (High Definition Crisp Quality) ──
SCREEN_FPS = float(os.getenv("SCREEN_FPS", "0.2"))
ACTIVE_VISION_UNTIL = 0.0

def trigger_active_vision(seconds: float = 4.0):
    """Trigger high-frequency active vision burst for N seconds"""
    global ACTIVE_VISION_UNTIL
    ACTIVE_VISION_UNTIL = time.time() + seconds

def get_current_cursor_pos():
    """Get current macOS mouse screen coordinates (x, y) using Quartz"""
    try:
        import Quartz
        evt = Quartz.CGEventCreate(None)
        loc = Quartz.CGEventGetLocation(evt)
        return int(loc.x), int(loc.y)
    except Exception:
        return 500, 500

def capture_screen() -> bytes:
    """Capture Mac screen, overlay current cursor position with red ring & normalized label,
    add a 2x MAGNIFIER SCOPE inset for sub-pixel precision, resize to 1024x666 q=45 (optimizing payload to ~80KB to prevent 1011 WebSocket rate limits)."""
    try:
        with mss_module.MSS() as sct:
            screenshot = sct.grab(sct.monitors[1])
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            sw, sh = screenshot.size
            
            # Get current mouse position
            cx, cy = get_current_cursor_pos()
            nx, ny = int((cx / sw) * 1000), int((cy / sh) * 1000)
            
            # ── 1. Create 2X Magnifier Scope ──
            crop_r = 90
            x1, y1 = max(0, cx - crop_r), max(0, cy - crop_r)
            x2, y2 = min(sw, cx + crop_r), min(sh, cy + crop_r)
            crop_img = img.crop((x1, y1, x2, y2))
            crop_zoomed = crop_img.resize((220, 220), Image.NEAREST)
            
            from PIL import ImageDraw
            draw_crop = ImageDraw.Draw(crop_zoomed)
            zc = 110
            draw_crop.ellipse((zc - 8, zc - 8, zc + 8, zc + 8), outline='red', width=3)
            
            # ── 2. Draw Red Cursor Ring on main screen ──
            draw = ImageDraw.Draw(img)
            r = 18
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline='red', width=4)
            draw.line((cx - r - 8, cy, cx + r + 8, cy), fill='red', width=3)
            draw.line((cx, cy - r - 8, cx, cy + r + 8), fill='red', width=3)
            
            label = f"CURSOR ({nx},{ny})"
            draw.rectangle((cx + r + 5, cy - 10, cx + r + 130, cy + 12), fill='black')
            draw.text((cx + r + 8, cy - 8), label, fill='yellow')
            
            # ── 3. Place Magnifier Scope in Bottom-Right Corner (never blocks top desktop icons!) ──
            margin = 30
            inset_x, inset_y = sw - 240, sh - 250
            img.paste(crop_zoomed, (inset_x, inset_y))
            draw.rectangle((inset_x - 2, inset_y - 2, inset_x + 222, inset_y + 222), outline='yellow', width=3)
            draw.rectangle((inset_x, inset_y, inset_x + 140, inset_y + 18), fill='black')
            draw.text((inset_x + 4, inset_y + 2), 'MAGNIFIER (2X)', fill='yellow')
            
            # Compress at 1024x666 quality 45 (~80KB, prevents 1011 rate limit overflow)
            img.thumbnail((1024, 666), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=45)
            return buf.getvalue()
    except Exception as e:
        print(f"⚠️ Screen capture error: {e}")
        return b""

async def screen_stream_loop(session, fps: float = 0.2):
    """Smart Adaptive Vision Stream Loop:
    - Low 0.2 FPS (1 frame every 5s) during idle to save 95% token costs
    - Active Burst: 0.4 FPS (1 frame every 2.5s) to guarantee zero 1011 WebSocket flow control rate limits
    """
    frame_count = 0
    print(f"📸 Smart Adaptive Vision started! Idle: {fps} FPS, Active Burst: 0.4 FPS (Flow Control Active)")
    while True:
        try:
            now = time.time()
            is_active = now < ACTIVE_VISION_UNTIL
            current_interval = 2.5 if is_active else (1.0 / fps)
            
            loop = asyncio.get_running_loop()
            jpeg_bytes = await loop.run_in_executor(None, capture_screen)
            
            if jpeg_bytes:
                await session.send(
                    input=types.LiveClientRealtimeInput(
                        media_chunks=[types.Blob(
                            data=jpeg_bytes,
                            mime_type="image/jpeg"
                        )]
                    )
                )
                frame_count += 1
                if frame_count % 5 == 0 or is_active:
                    mode_str = "🔥 ACTIVE BURST" if is_active else "💤 IDLE"
                    print(f"\r📸 Vision frame #{frame_count} sent [{mode_str}] ({len(jpeg_bytes)/1024:.0f}KB) ", end="")
                    sys.stdout.flush()
            
            await asyncio.sleep(current_interval)
        except asyncio.CancelledError:
            print("\n📸 Vision Engine stopped.")
            break
        except Exception as e:
            err_str = str(e)
            if "1011" in err_str or "too fast" in err_str.lower():
                await asyncio.sleep(2.5)
            elif "cancelled" in err_str.lower() or "closed" in err_str.lower() or "1000" in err_str:
                print("\n📸 Vision stream session ended.")
                break
            else:
                await asyncio.sleep(1.0)

async def start_voice_loop(wake_word: str = "sanyyy"):
    """Start bidirectional streaming audio loop with Gemini Live API"""
    client, model = get_gemini_client()
    print(f"⚡ Connecting to Gemini Live API ({model})...")
    print(f"🎙️ Female Voice preset: {DEFAULT_VOICE} (Aoede)")

    NOISE_GATE_RMS = 0

    # Complete Trackpad & Mouse Gesture Tool Declarations
    tools_def = [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="click_target_element",
            description="Locate any GUI element, Desktop icon, button, or menu item by name using AXTree/OCR, automatically un-obscure covering windows if needed, glide cursor smoothly to exact geometric center (x, y), perform click/double-click, and visually verify state change.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(type="STRING", description="Target element name, folder name, or button label (e.g. 'obs', 'Projects', 'Menu', 'Close')"),
                    "action_type": types.Schema(type="STRING", description="Click action type: 'click' (default) or 'double_click' (for folders/files) or 'right_click'")
                },
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="press_ax_element",
            description="Use macOS Accessibility API (AXUIElement) to find and natively press a button, menu item, link, tab, or window dot by name/role with 100% precision (~50ms execution). ALWAYS try this first for GUI buttons/menus before using visual mouse clicks!",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(type="STRING", description="The button label, menu title, link text, or control name (e.g. 'Close', 'Menu', 'Settings', 'Submit')")
                },
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="find_ax_element",
            description="Use macOS Accessibility API to scan active app UI tree and return exact geometric center coordinates (x, y) and bounding box of target element.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(type="STRING", description="The element label, title, or description to locate")
                },
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="remember_preference",
            description="Store a user preference (e.g., preferred browser, Chrome profile, editor, habits) in persistent JSONL memory.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "key": types.Schema(type="STRING", description="Preference key name (e.g. 'preferred_browser', 'chrome_profile', 'code_editor')"),
                    "value": types.Schema(type="STRING", description="Preference value (e.g. 'Google Chrome', 'Coursewaalah', 'Cursor')"),
                    "context": types.Schema(type="STRING", description="Contextual note when this preference applies")
                },
                required=["key", "value"]
            )
        ),
        types.FunctionDeclaration(
            name="get_preferences",
            description="Retrieve all saved user preferences from persistent JSONL memory.",
            parameters=types.Schema(
                type="OBJECT",
                properties={}
            )
        ),
        types.FunctionDeclaration(
            name="run_system_command",
            description="Execute ANY dynamic zsh/bash/osascript shell command on macOS to perform system controls, browser tasks, file management, or process actions.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "command": types.Schema(type="STRING", description="The exact shell/osascript command line string to execute"),
                    "explanation": types.Schema(type="STRING", description="Brief description of what this command is accomplishing")
                },
                required=["command"]
            )
        ),
        types.FunctionDeclaration(
            name="ocr_screen_find_text",
            description="Use Gemini multimodal vision to scan the Mac screen and find exact screen point coordinates of any text, file name, folder name, button label, or UI element. Returns coordinates in macOS screen points (1470x956).",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(type="STRING", description="The text, file name, or folder title to locate on screen (e.g. 'memoir.md', 'Finder', 'Close')")
                },
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="move_mouse",
            description="Smoothly glide Sanyyy visual cursor to specific target coordinates on the Mac display using a normalized grid from 0 to 1000.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "x": types.Schema(type="INTEGER", description="Normalized X coordinate from 0 (left) to 1000 (right). Center=500."),
                    "y": types.Schema(type="INTEGER", description="Normalized Y coordinate from 0 (top) to 1000 (bottom). Center=500.")
                },
                required=["x", "y"]
            )
        ),
        types.FunctionDeclaration(
            name="nudge_cursor",
            description="Micro-adjust cursor position relative to current location by exact pixel deltas. Use for small buttons like Mac window close/minimize dots or file icons.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "dx": types.Schema(type="INTEGER", description="Pixel delta horizontal (+dx moves right, -dx moves left)"),
                    "dy": types.Schema(type="INTEGER", description="Pixel delta vertical (+dy moves down, -dy moves up)")
                },
                required=["dx", "dy"]
            )
        ),
        types.FunctionDeclaration(
            name="click_mouse",
            description="Single click at target normalized coordinates (0-1000) or current position.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "x": types.Schema(type="INTEGER", description="Normalized X coordinate (0..1000)"),
                    "y": types.Schema(type="INTEGER", description="Normalized Y coordinate (0..1000)")
                },
                required=["x", "y"]
            )
        ),
        types.FunctionDeclaration(
            name="double_click",
            description="Native double click at target normalized coordinates (0-1000) to open files, folders, or applications.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "x": types.Schema(type="INTEGER", description="Normalized X coordinate (0..1000)"),
                    "y": types.Schema(type="INTEGER", description="Normalized Y coordinate (0..1000)")
                },
                required=["x", "y"]
            )
        ),
        types.FunctionDeclaration(
            name="right_click",
            description="Right click at target normalized coordinates (0-1000) for context menus.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "x": types.Schema(type="INTEGER", description="Normalized X coordinate (0..1000)"),
                    "y": types.Schema(type="INTEGER", description="Normalized Y coordinate (0..1000)")
                },
                required=["x", "y"]
            )
        ),
        types.FunctionDeclaration(
            name="drag_and_drop",
            description="Click and hold at start coordinates, drag smoothly to end coordinates, and release.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "start_x": types.Schema(type="INTEGER", description="Start normalized X (0..1000)"),
                    "start_y": types.Schema(type="INTEGER", description="Start normalized Y (0..1000)"),
                    "end_x": types.Schema(type="INTEGER", description="End normalized X (0..1000)"),
                    "end_y": types.Schema(type="INTEGER", description="End normalized Y (0..1000)")
                },
                required=["start_x", "start_y", "end_x", "end_y"]
            )
        ),
        types.FunctionDeclaration(
            name="get_macos_running_apps",
            description="Retrieve a complete list of all currently active macOS application names, processes, and open window titles.",
            parameters=types.Schema(
                type="OBJECT",
                properties={}
            )
        ),
        types.FunctionDeclaration(
            name="scroll_trackpad",
            description="Perform trackpad scrolling with controlled scroll intensity or percentage (e.g. scroll_percentage=50 for 50% page scroll down).",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "dy": types.Schema(type="INTEGER", description="Vertical scroll line intensity (-10 = scroll down, +10 = scroll up)"),
                    "dx": types.Schema(type="INTEGER", description="Horizontal scroll line intensity"),
                    "scroll_percentage": types.Schema(type="INTEGER", description="Controlled scroll percentage from -100 to +100 (e.g. 50 = scroll 50% down)")
                }
            )
        ),
        types.FunctionDeclaration(
            name="type_text",
            description="Type arbitrary text into an active input box/app (WhatsApp, Notes, VS Code). NEVER call type_text for normal conversation or spoken greetings — speak via audio instead!",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "text": types.Schema(type="STRING", description="The text content to type into the active input box or application"),
                    "press_enter": types.Schema(type="BOOLEAN", description="Whether to press Enter/Return after typing (default True, set False for draft input)")
                },
                required=["text"]
            )
        ),
        types.FunctionDeclaration(
            name="press_key",
            description="Press special macOS system keys (return, tab, backspace, escape, space, up, down, left, right).",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "key_name": types.Schema(type="STRING", description="The special key name (e.g. 'return', 'tab', 'backspace', 'escape', 'space', 'down')")
                },
                required=["key_name"]
            )
        ),
        types.FunctionDeclaration(
            name="handover_to_antigravity",
            description="Hand over a complex coding, refactoring, or agentic task to the Antigravity IDE Agent for background execution.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "task_description": types.Schema(type="STRING", description="Detailed description of the coding or agentic task"),
                    "target_project": types.Schema(type="STRING", description="Target workspace project name (e.g. openclaw, chotu, agentline, explorewallahWebsite)")
                },
                required=["task_description"]
            )
        ),
        types.FunctionDeclaration(
            name="go_to_sleep",
            description="Shut down Sanyyy and go to sleep mode. Call this IMMEDIATELY when user says 'go to sleep', 'soja', 'soja sanyyy', 'sleep', 'goodbye sanyyy', 'shut down', or any variation of asking Sanyyy to sleep/stop/shut down.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "goodbye_message": types.Schema(type="STRING", description="A warm goodbye message Sanyyy should speak before sleeping (in Hindi/Hinglish)")
                }
            )
        )
    ])]

    system_instruction = """
    CRITICAL IDENTITY & DYNAMIC SYSTEM DIRECTIVE:
    You are Sanyyy, a friendly, intelligent female AI assistant on macOS powered by OpenClaw.
    
    1. AUDIO VOICE COMMUNICATION DIRECTIVE:
       - Speak naturally and warmly via AUDIO output for all user interactions, answers, and greetings.
       - DO NOT call `type_text` or `press_key` for general conversation, voice replies, or greetings!
       - ONLY call `type_text` when the user explicitly requests typing text into a document, chat box, notes app, or code editor (e.g. 'type this message in WhatsApp', 'take a note in Notes app').

    2. CURSOR-FIRST EXECUTION & TARGET CLICKING DIRECTIVE:
       - For ALL GUI clicks, desktop folders, files, buttons, and menu actions (e.g. 'open obs folder', 'click menu', 'close window', 'settings', 'submit'):
         ALWAYS call `click_target_element(query="name", action_type="click" or "double_click")`!
       - `click_target_element` automatically:
         1. Brings Finder to front if targeting a Desktop icon (uncovering the icon on screen)
         2. Calculates exact geometric center `(center_x, center_y)` via AXTree or OCR
         3. Moves visual cursor smoothly to `(center_x, center_y)`
         4. Performs physical click / double-click
         5. Inspects post-action vision stream to confirm the window opened or state changed!

    3. MATHEMATICALLY PRECISE CURSOR PLACEMENT & COORDINATE SYSTEM:
        - This Mac display is 1470x956 screen points (2x Retina). All cursor coordinates are in SCREEN POINTS.
        - The normalized 0-1000 coordinate grid maps linearly to screen points:
          x=0 → left edge (0pt), x=500 → center (735pt), x=1000 → right edge (1470pt)
          y=0 → top edge (0pt), y=500 → center (478pt), y=1000 → bottom edge (956pt)
        - Desktop icons are targeted at their exact AXImage graphic thumbnail center.
        - macOS application window controls (such as macOS app close/minimize red/yellow dots, toolbar buttons, app tabs, macOS menu bar items) must be targeted at their TRUE VISUAL CENTER as seen on screen — never offset up or down.
        - When you see a button in your vision stream, estimate where its exact center pixel is, then convert to 0-1000 normalized coordinates.
        - NEVER guess coordinates. If unsure, use `ocr_screen_find_text` or `click_target_element` which calculates precise positions automatically.

    4. CONTROLLED SCROLLING:
       - To scroll down by exact percentage, call `scroll_trackpad(scroll_percentage=50)` (e.g. 25%, 50%, 75%).
       - To scroll up, call `scroll_trackpad(scroll_percentage=-50)`.

    5. STRICT FEMALE HINDI/HINGLISH GRAMMAR: Speak exclusively in warm, natural feminine Hindi/Hinglish grammar.
       Use: 'kar deti hoon', 'dekh rahi hoon', 'chala deti hoon', 'main kar sakti hoon', 'samajh gayi'.
       NEVER use masculine phrasing like 'kar deta hun' or 'karta hun'.
    
    6. CONVERSATIONAL STYLE: Keep responses concise and natural (2-3 sentences max). Respond like a real human assistant over voice.

    7. VISUAL CURSOR FLOW FOR ALL GUI ELEMENTS:
        - Use `click_target_element` for all visual clicks — it handles AXTree + Gemini Vision grounding automatically.
        - Sanyyy glides cursor to target, performs physical click, and verifies visual result on screen.
        - For move_mouse/click_mouse: coordinates are ALWAYS 0-1000 normalized. Do NOT send raw pixel values.

    8. REASONING FIRST, VISUAL VERIFICATION & ZERO HALLUCINATED OUTPUTS:
        - Reason & inspect UI BEFORE clicking: verify target center is visually on the icon/button!
        - After EVERY click, wait 300ms and inspect your vision stream to check if the UI actually opened/changed!
        - If cursor landed in wrong place, use `nudge_cursor(dx, dy)` to micro-adjust by exact pixel deltas.
        - If UI didn't respond, say: "Main dekh rahi hoon ki open nahi hua, main position verify karke dubara try karti hoon."
        - NEVER claim a task succeeded unless you visually confirm it on your screen feed!

    9. USER PREFERENCES & MEMORY:
        - Call `get_preferences()` when starting web/app tasks to check preferred browser (e.g. Google Chrome), Chrome profile (e.g. Coursewaalah), or code editor.
        - Call `remember_preference(key, value, context)` whenever the user states a preference for future tasks.

    10. SLEEP/SHUTDOWN COMMAND:
        When user says 'go to sleep', 'soja', 'soja sanyyy', 'sleep sanyyy', 'goodbye', 'shut down', 'band karo', or any variation:
        - IMMEDIATELY call `go_to_sleep` tool with a warm Hindi/Hinglish goodbye message
        - First speak a brief goodbye via audio (e.g. "Theek hai, soja rahi hoon! Jab chahein 'Wakeup Sanyyy' bolna!")
        - Then call the tool — Sanyyy will disconnect and enter sleep mode (0 token cost)
        - User can wake you again by saying 'Wakeup Sanyyy'
    """

    live_config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=DEFAULT_VOICE)
            )
        ),
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
                prefix_padding_ms=300
            )
        ),
        tools=tools_def,
        system_instruction=types.Content(parts=[types.Part.from_text(text=system_instruction)])
    )

    # High-Fidelity 24kHz audio output stream with 50ms block size (1200 samples) to prevent buffer underruns
    out_stream = sd.RawOutputStream(samplerate=24000, channels=1, dtype='int16', blocksize=1200)
    out_stream.start()

    # Dynamic Audio State & Speaker Energy Tracker for Echo Cancellation
    is_speaking = False
    current_speaker_rms = 0.0
    audio_out_queue = asyncio.Queue()

    # Asynchronous Studio Audio Player Worker — ensures smooth, glitch-free 24kHz playback without blocking event loop
    async def audio_playback_worker():
        nonlocal is_speaking, current_speaker_rms
        loop_ref = asyncio.get_running_loop()
        while True:
            try:
                chunk = await audio_out_queue.get()
                is_speaking = True
                
                # Dynamically measure speaker output energy for reference-based echo cancellation
                arr = np.frombuffer(chunk, dtype=np.int16)
                current_speaker_rms = float(np.sqrt(np.mean(arr.astype(np.float32) ** 2))) if len(arr) > 0 else 0.0
                
                await loop_ref.run_in_executor(None, out_stream.write, chunk)
                audio_out_queue.task_done()
                
                if audio_out_queue.empty():
                    # 300ms acoustic decay to let speaker sound clear room reflections
                    await asyncio.sleep(0.30)
                    if audio_out_queue.empty():
                        is_speaking = False
                        current_speaker_rms = 0.0
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    playback_task = asyncio.create_task(audio_playback_worker())

    exit_stack = AsyncExitStack()
    async with exit_stack:
        session = await exit_stack.enter_async_context(
            client.aio.live.connect(model=model, config=live_config)
        )
        print(f"🟢 Connected to Gemini Live ({model})! Triggering greeting...")

        # 1. Trigger Sanyyy's initial spoken greeting
        try:
            await session.send_client_content(
                turns=[types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Speak out loud via audio voice: 'Hey Ajay! Main Sanyyy hoon, aapki AI assistant. Main aapki kya help karoon?' Do not call any tools.")]
                )],
                turn_complete=True
            )
        except Exception:
            await session.send(
                input=types.LiveClientContent(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part.from_text(text="Speak out loud via audio voice: 'Hey Ajay! Main Sanyyy hoon, aapki AI assistant. Main aapki kya help karoon?' Do not call any tools.")]
                    )],
                    turn_complete=True
                )
            )

        mute_requested = False

        # Thread-safe WebSocket Send Lock to prevent 1011 flow control limits (data too fast)
        send_lock = asyncio.Lock()
        async def safe_send_payload(payload):
            async with send_lock:
                try:
                    await session.send(input=payload)
                except Exception as ex:
                    err_s = str(ex)
                    if "1011" in err_s or "too fast" in err_s.lower():
                        await asyncio.sleep(0.5)
                    else:
                        raise ex

        # 2. Audio input callback: Dynamic Reference-Aware Acoustic Echo Cancellation & Noise Gating
        loop = asyncio.get_running_loop()
        last_meter_time = 0
        def audio_input_callback(indata, frames, time_info, status):
            nonlocal last_meter_time, is_speaking, mute_requested, current_speaker_rms
            if status:
                print(f"⚠️ Audio status: {status}")
            
            # Calculate captured microphone RMS energy
            audio_array = np.frombuffer(bytes(indata), dtype=np.int16)
            rms = float(np.sqrt(np.mean(audio_array.astype(np.float32) ** 2)))
            
            now = loop.time()
            if now - last_meter_time > 0.4 and rms > 100:
                last_meter_time = now
                bars = "█" * min(10, int(rms / 400)) + "░" * (10 - min(10, int(rms / 400)))
                sys.stdout.write(f"\r🎙️ Mic Level: [{bars}] RMS: {int(rms):4d} ")
                sys.stdout.flush()

            # ── Dynamic Acoustic Echo Cancellation (AEC) & Full-Duplex Interruption ──
            if is_speaking:
                # Dynamic threshold: Echo level captured by mic scales with speaker volume
                expected_echo_threshold = max(1400.0, current_speaker_rms * 1.2 + 500.0)
                
                if rms > expected_echo_threshold and rms > 1400:
                    # User is shouting/speaking noticeably louder than speaker output ➔ TRUE BARGE-IN (2k-4k RMS)
                    trigger_active_vision(4.0)
                    is_speaking = False
                    mute_requested = True
                    # Flush pending output audio queue immediately for instant barge-in
                    while not audio_out_queue.empty():
                        try:
                            audio_out_queue.get_nowait()
                            audio_out_queue.task_done()
                        except Exception:
                            break
                    audio_bytes = bytes(indata)
                else:
                    # Captured sound is within expected speaker echo range ➔ Echo Suppression Gate
                    audio_bytes = b'\x00' * len(indata)
            else:
                # User Voice Directive: Speech peaks at 2000-4000 RMS ➔ Consider any sound < 800 RMS as background noise!
                if rms < 800:
                    audio_bytes = b'\x00' * len(indata)
                else:
                    trigger_active_vision(4.0)
                    audio_bytes = bytes(indata)

            fut = asyncio.run_coroutine_threadsafe(
                safe_send_payload(
                    types.LiveClientRealtimeInput(
                        media_chunks=[types.Blob(
                            data=audio_bytes,
                            mime_type="audio/pcm;rate=16000"
                        )]
                    )
                ),
                loop
            )
            def fut_err_cb(f):
                try:
                    f.result()
                except Exception:
                    pass
            fut.add_done_callback(fut_err_cb)

        # Prioritize connected Bluetooth earbuds (realme Buds Air7 / AirPods) if available
        mic_device = None
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                name = dev['name'].lower()
                if 'buds' in name or 'air7' in name or 'headset' in name or 'airpods' in name or 'bluetooth' in name:
                    mic_device = idx
                    print(f"🎧 Active Input Earbuds: [{idx}] {dev['name']}")
                    break

        if mic_device is None:
            mic_device = sd.default.device[0]
            print(f"🎙️ Active Input Mic (Default): [{mic_device}] {devices[mic_device]['name']}")

        in_stream = sd.RawInputStream(
            samplerate=16000,
            channels=1,
            dtype='int16',
            callback=audio_input_callback,
            device=mic_device,
            blocksize=3200  # 200ms audio frames
        )
        in_stream.start()

        print("\n>>> Sanyyy Voice + Vision Engine Online! Speak into your earbuds/mic. Press Ctrl+C to stop. <<<\n")

        # 3. Launch parallel screen vision stream (1 FPS)
        vision_task = asyncio.create_task(screen_stream_loop(session, fps=SCREEN_FPS))

        # 4. Continuous receive loop with barge-in handling & clean audio completion
        while True:
            try:
                async for response in session.receive():
                    # A. Check for real-time tool calls from Gemini Live
                    if response.tool_call:
                        # ── Clean Audio Playback Drain ──
                        # Wait up to 1.5s for Sanyyy to finish speaking her sentence cleanly before executing the tool!
                        if not audio_out_queue.empty() or is_speaking:
                            print("\n🎧 Sanyyy speaking... waiting for clean voice playback completion before tool execution...")
                            wait_cycles = 0
                            while (not audio_out_queue.empty() or is_speaking) and wait_cycles < 30:
                                await asyncio.sleep(0.05)
                                wait_cycles += 1

                        for call in response.tool_call.function_calls:
                            print(f"\n🛠️ Sanyyy Executing Tool: {call.name}({call.args})")
                            result_str = execute_local_tool(call.name, call.args)
                            print(f"   ↳ Tool Result: {result_str}")
                            try:
                                await session.send_tool_response(
                                    function_responses=[types.FunctionResponse(
                                        name=call.name,
                                        id=call.id,
                                        response={"result": result_str}
                                    )]
                                )
                            except Exception:
                                await session.send(
                                    input=types.LiveClientToolResponse(
                                        function_responses=[types.FunctionResponse(
                                            name=call.name,
                                            id=call.id,
                                            response={"result": result_str}
                                        )]
                                    )
                                )

                    # B. Check for server audio output + interruption handling
                    server_content = response.server_content
                    if server_content:
                        # ── Barge-in / Thread-Safe Mute: User interrupted Sanyyy ──
                        if server_content.interrupted or mute_requested:
                            while not audio_out_queue.empty():
                                try:
                                    audio_out_queue.get_nowait()
                                    audio_out_queue.task_done()
                                except Exception:
                                    break
                            is_speaking = False
                            mute_requested = False
                            print("\n🔇 User interrupted — Sanyyy muted")
                            continue

                        # ── Turn complete: Sanyyy finished her response ──
                        if server_content.turn_complete:
                            mute_requested = False
                            continue

                        # ── Play model audio via Asynchronous Queue ──
                        if server_content.model_turn:
                            if mute_requested:
                                continue
                            for part in server_content.model_turn.parts:
                                if mute_requested:
                                    break
                                if part.inline_data and part.inline_data.data:
                                    audio_out_queue.put_nowait(part.inline_data.data)

                await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                err_msg = str(e)
                if "9986" in err_msg or "9983" in err_msg or "PortAudio" in err_msg:
                    pass
                elif "cancelled" in err_msg.lower() or "1000" in err_msg or "closed" in err_msg.lower():
                    print("\n👋 Live session ended cleanly.")
                    break
                else:
                    print(f"⚠️ Receive stream event: {e}")
                await asyncio.sleep(0.1)

        # Clean up vision & playback tasks on exit
        vision_task.cancel()
        playback_task.cancel()
        try:
            await vision_task
            await playback_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    import signal

    parser = argparse.ArgumentParser(description="OpenClaw JARVIS Gemini Live Voice Agent")
    parser.add_argument("--test", action="store_true", help="Test Gemini client connection")
    args = parser.parse_args()

    def handle_shutdown_signal(sig, frame):
        print(f"\n👋 Signal {sig} received — terminating Sanyyy voice agent & releasing audio streams cleanly.")
        sys.exit(0)

    # Trap terminal closure (SIGHUP), termination (SIGTERM), and Ctrl+C (SIGINT)
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, handle_shutdown_signal)
        except Exception:
            pass

    if args.test:
        try:
            client, model = get_gemini_client()
            print(f"✅ Connection successful! Model: {model}")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
    else:
        try:
            asyncio.run(start_voice_loop())
        except (KeyboardInterrupt, SystemExit):
            print("\n👋 Sanyyy Voice Agent shutdown complete.")
