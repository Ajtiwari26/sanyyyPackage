#!/usr/bin/env python3
"""
Sanyyy Custom Trackpad & Mouse Gesture Engine for macOS
Provides native Quartz gesture controls:
- Smooth glide cursor movement
- Relative micro-nudge adjustment (exact pixel deltas)
- Single click, Double click (clickState=2), Right click
- Drag and Drop (click and hold + smooth drag)
- Trackpad two-finger scrolling (vertical/horizontal)
"""

import sys
import time
import math
import subprocess

try:
    import Quartz
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyobjc-framework-Quartz"])
    import Quartz

def get_cursor_position():
    """Get current macOS mouse screen coordinates (x, y)"""
    evt = Quartz.CGEventCreate(None)
    loc = Quartz.CGEventGetLocation(evt)
    return int(loc.x), int(loc.y)

def calculate_euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points: sqrt((x2 - x1)^2 + (y2 - y1)^2)"""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def move_cursor_smooth(target_x: int, target_y: int, duration: float = 0.30, steps: int = 15):
    """Smoothly glide mouse cursor to target coordinates with cubic easing and Euclidean vector tracking"""
    start_x, start_y = get_cursor_position()
    dist = calculate_euclidean_distance(start_x, start_y, target_x, target_y)
    
    for i in range(1, steps + 1):
        t = i / steps
        ease_t = 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2
        
        curr_x = start_x + (target_x - start_x) * ease_t
        curr_y = start_y + (target_y - start_y) * ease_t
        
        point = Quartz.CGPoint(curr_x, curr_y)
        move_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, point, Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_evt)
        time.sleep(duration / steps)
    
    print(f"🌸 Sanyyy Euclidean Vector Glide: ({start_x}, {start_y}) ➔ ({target_x}, {target_y}) | Δx={target_x - start_x}px, Δy={target_y - start_y}px | Distance={dist:.1f}px")

def nudge_cursor(dx: int, dy: int):
    """Micro-nudge cursor relative to current position by dx (right/left) and dy (down/up) pixels using Euclidean vector calculation"""
    cx, cy = get_cursor_position()
    tx, ty = cx + dx, cy + dy
    dist = calculate_euclidean_distance(cx, cy, tx, ty)
    point = Quartz.CGPoint(tx, ty)
    move_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, point, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_evt)
    print(f"🌸 Sanyyy Euclidean Micro-Nudge: ({cx}, {cy}) ➔ ({tx}, {ty}) | Δx={dx}px, Δy={dy}px | Distance={dist:.1f}px")

def click_bounds_center(x: int, y: int, width: int, height: int):
    """Calculate exact geometric center of UI element (x + w/2, y + h/2) and click at center"""
    center_x = int(x + width / 2.0)
    center_y = int(y + height / 2.0)
    print(f"🎯 Target Bounding Box: ({x},{y}, {width}x{height}) ➔ Geometric Center: ({center_x}, {center_y})")
    single_click(center_x, center_y)

def single_click(x: int = None, y: int = None):
    """Perform a single left mouse click"""
    if x is not None and y is not None:
        move_cursor_smooth(x, y)
    cx, cy = get_cursor_position()
    point = Quartz.CGPoint(cx, cy)
    
    down_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
    up_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
    
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_evt)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_evt)
    print(f"🌸 Sanyyy Single Clicked at ({cx}, {cy})")

def double_click(x: int = None, y: int = None):
    """Perform a native double click with clickState=2 (opens files, folders, apps)"""
    if x is not None and y is not None:
        move_cursor_smooth(x, y)
    cx, cy = get_cursor_position()
    point = Quartz.CGPoint(cx, cy)
    
    # Click 1
    d1 = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
    u1 = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventSetIntegerValueField(d1, Quartz.kCGMouseEventClickState, 1)
    Quartz.CGEventSetIntegerValueField(u1, Quartz.kCGMouseEventClickState, 1)
    
    # Click 2
    d2 = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
    u2 = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventSetIntegerValueField(d2, Quartz.kCGMouseEventClickState, 2)
    Quartz.CGEventSetIntegerValueField(u2, Quartz.kCGMouseEventClickState, 2)
    
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, d1)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, u1)
    time.sleep(0.04)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, d2)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, u2)
    print(f"🌸 Sanyyy Double Clicked at ({cx}, {cy})")

def right_click(x: int = None, y: int = None):
    """Perform a right click (context menu)"""
    if x is not None and y is not None:
        move_cursor_smooth(x, y)
    cx, cy = get_cursor_position()
    point = Quartz.CGPoint(cx, cy)
    
    down_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventRightMouseDown, point, Quartz.kCGMouseButtonRight)
    up_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventRightMouseUp, point, Quartz.kCGMouseButtonRight)
    
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_evt)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_evt)
    print(f"🌸 Sanyyy Right Clicked at ({cx}, {cy})")

def drag_and_drop(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.4, steps: int = 20):
    """Click and hold at start coordinates, drag smoothly to end coordinates, and release"""
    move_cursor_smooth(start_x, start_y)
    dist = calculate_euclidean_distance(start_x, start_y, end_x, end_y)
    
    start_pt = Quartz.CGPoint(start_x, start_y)
    down_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, start_pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_evt)
    time.sleep(0.05)
    
    for i in range(1, steps + 1):
        t = i / steps
        ease_t = 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2
        cx = start_x + (end_x - start_x) * ease_t
        cy = start_y + (end_y - start_y) * ease_t
        pt = Quartz.CGPoint(cx, cy)
        drag_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, pt, Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag_evt)
        time.sleep(duration / steps)
        
    end_pt = Quartz.CGPoint(end_x, end_y)
    up_evt = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, end_pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_evt)
    print(f"🌸 Sanyyy Dragged and Dropped ({start_x}, {start_y}) ➔ ({end_x}, {end_y}) | Distance={dist:.1f}px")

def scroll_trackpad(dy: int = -10, dx: int = 0, scroll_percentage: int = None):
    """Perform trackpad scrolling with controlled scroll intensity or percentage (e.g. scroll_percentage=50 for 50% page scroll down)"""
    if scroll_percentage is not None:
        # Convert percentage to line count (100% = 40 lines scroll)
        dy = int((scroll_percentage / 100.0) * -40.0)
        if dy == 0:
            dy = -1 if scroll_percentage > 0 else 1

    # Send multi-step scroll events for smooth, controlled momentum
    steps = max(1, abs(dy) // 5)
    step_dy = dy // steps if steps > 0 else dy
    for _ in range(steps):
        scroll_evt = Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitLine, 2, step_dy, dx)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, scroll_evt)
        time.sleep(0.03)
        
    print(f"🌸 Sanyyy Controlled Trackpad Scroll [dy={dy}, dx={dx}, percentage={scroll_percentage}%]")

def type_text(text: str, press_enter: bool = True):
    """Type arbitrary text into the focused active window using macOS pbcopy + Cmd+V paste for 100% Unicode & speed accuracy"""
    try:
        proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        proc.communicate(text.encode('utf-8'))
        time.sleep(0.05)
        
        cmd = 'tell application "System Events" to keystroke "v" using {command down}'
        subprocess.run(['osascript', '-e', cmd], check=True)
        time.sleep(0.05)
        
        if press_enter:
            enter_cmd = 'tell application "System Events" to key code 36'
            subprocess.run(['osascript', '-e', enter_cmd], check=True)
            
        print(f"🌸 Sanyyy Typed Text: '{text[:40]}...' (Enter={press_enter})")
    except Exception as e:
        print(f"⚠️ Error typing text: {e}")

def press_key(key_name: str):
    """Press macOS system special keys (return, tab, backspace, escape, space, up, down, left, right)"""
    key_codes = {
        "return": 36, "enter": 36,
        "tab": 48,
        "space": 49,
        "backspace": 51, "delete": 51,
        "escape": 53, "esc": 53,
        "left": 123, "right": 124, "down": 125, "up": 126
    }
    key_lower = key_name.lower()
    if key_lower in key_codes:
        code = key_codes[key_lower]
        cmd = f'tell application "System Events" to key code {code}'
        subprocess.run(['osascript', '-e', cmd], check=True)
        print(f"🌸 Sanyyy Pressed Key: '{key_name}' (code {code})")
    else:
        cmd = f'tell application "System Events" to keystroke "{key_name}"'
        subprocess.run(['osascript', '-e', cmd], check=True)
        print(f"🌸 Sanyyy Keystroke: '{key_name}'")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        cmd = sys.argv[1].lower()
        if cmd == "move" and len(sys.argv) >= 4:
            move_cursor_smooth(int(sys.argv[2]), int(sys.argv[3]))
        elif cmd == "nudge" and len(sys.argv) >= 4:
            nudge_cursor(int(sys.argv[2]), int(sys.argv[3]))
        elif cmd == "click":
            x = int(sys.argv[2]) if len(sys.argv) >= 4 else None
            y = int(sys.argv[3]) if len(sys.argv) >= 4 else None
            single_click(x, y)
        elif cmd == "center_click" and len(sys.argv) >= 6:
            click_bounds_center(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
        elif cmd == "double_click":
            x = int(sys.argv[2]) if len(sys.argv) >= 4 else None
            y = int(sys.argv[3]) if len(sys.argv) >= 4 else None
            double_click(x, y)
        elif cmd == "right_click":
            x = int(sys.argv[2]) if len(sys.argv) >= 4 else None
            y = int(sys.argv[3]) if len(sys.argv) >= 4 else None
            right_click(x, y)
        elif cmd == "drag" and len(sys.argv) >= 6:
            drag_and_drop(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
        elif cmd == "scroll" and len(sys.argv) >= 3:
            dy = int(sys.argv[2])
            dx = int(sys.argv[3]) if len(sys.argv) >= 4 else 0
            pct = int(sys.argv[4]) if len(sys.argv) >= 5 else None
            scroll_trackpad(dy, dx, pct)
        elif cmd == "type" and len(sys.argv) >= 3:
            text = sys.argv[2]
            press_enter = sys.argv[3].lower() == "true" if len(sys.argv) >= 4 else True
            type_text(text, press_enter)
        elif cmd == "key" and len(sys.argv) >= 3:
            press_key(sys.argv[2])
        else:
            # Fallback legacy mode: (x, y) single click
            if len(sys.argv) >= 3:
                single_click(int(sys.argv[1]), int(sys.argv[2]))
    else:
        cx, cy = get_cursor_position()
        print(f"Current Cursor Position: ({cx}, {cy})")
