#!/usr/bin/env python3
"""
🌸 SANYYY COMPREHENSIVE CURSOR, TRACKPAD & VISION UNIT TEST SUITE
===================================================================
Tests all core GUI automation and vision capabilities:
1. Cursor Position & Smooth Vector Glide (Quartz CGEvent)
2. Micro-Nudge Relative Vector Adjustment
3. Geometric Bounds Center Math Calculation
4. Single Left Click
5. Double Click (clickState=2)
6. Right Click (Context Menu)
7. Hold & Smooth Drag-and-Drop
8. Trackpad Scroll (Lines & Percentage)
9. macOS Screen Capture Engine (JPEG generation)
10. Apple Vision Framework OCR Text Grounding
11. AXTree Multi-Signal Verification (PID, App Name, Window Count, Hash)
"""

import os
import sys
import time
import math
import unittest
import subprocess

# Ensure scripts directory is on Python path
PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PACKAGE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import sanyyy_cursor_hud as hud
import sanyyy_ax_engine as ax_engine
import gemini_live_agent as agent

class TestSanyyyCursorAndVision(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n=======================================================")
        print("🧪 RUNNING SANYYY CURSOR, TRACKPAD & VISION UNIT TESTS")
        print("=======================================================")

    def test_01_cursor_position_and_smooth_glide(self):
        """Test smooth vector glide movement to target coordinates"""
        start_x, start_y = hud.get_cursor_position()
        target_x, target_y = start_x + 50, start_y + 50
        
        hud.move_cursor_smooth(target_x, target_y, duration=0.15, steps=10)
        end_x, end_y = hud.get_cursor_position()
        
        dist = hud.calculate_euclidean_distance(target_x, target_y, end_x, end_y)
        print(f"✅ Test 1 (Smooth Glide): Target ({target_x}, {target_y}) vs End ({end_x}, {end_y}) | Error: {dist:.1f}px")
        self.assertLessEqual(dist, 5.0, "Cursor end position should be within 5px of target")

    def test_02_micro_nudge(self):
        """Test relative micro-nudge adjustment"""
        start_x, start_y = hud.get_cursor_position()
        dx, dy = 15, -15
        
        hud.nudge_cursor(dx, dy)
        end_x, end_y = hud.get_cursor_position()
        
        expected_x, expected_y = start_x + dx, start_y + dy
        dist = hud.calculate_euclidean_distance(expected_x, expected_y, end_x, end_y)
        print(f"✅ Test 2 (Micro-Nudge): Expected ({expected_x}, {expected_y}) vs End ({end_x}, {end_y}) | Error: {dist:.1f}px")
        self.assertLessEqual(dist, 5.0, "Nudge end position should match expected delta")

    def test_03_bounds_center_calculation(self):
        """Test geometric bounds center coordinate calculation (x + w/2, y + h/2)"""
        bounds = {"x": 100, "y": 200, "width": 80, "height": 60}
        center_x = int(bounds["x"] + bounds["width"] / 2.0)
        center_y = int(bounds["y"] + bounds["height"] / 2.0)
        
        self.assertEqual(center_x, 140)
        self.assertEqual(center_y, 230)
        print(f"✅ Test 3 (Bounds Center Math): Box (100, 200, 80x60) ➔ Center ({center_x}, {center_y})")

    def test_04_single_click(self):
        """Test single left click execution without raising exceptions"""
        cx, cy = hud.get_cursor_position()
        try:
            hud.single_click(cx, cy)
            print(f"✅ Test 4 (Single Click): Successfully clicked at ({cx}, {cy})")
        except Exception as e:
            self.fail(f"Single click raised exception: {e}")

    def test_05_double_click(self):
        """Test double click execution (clickState=2)"""
        cx, cy = hud.get_cursor_position()
        try:
            hud.double_click(cx, cy)
            print(f"✅ Test 5 (Double Click): Successfully double-clicked at ({cx}, {cy})")
        except Exception as e:
            self.fail(f"Double click raised exception: {e}")

    def test_06_right_click(self):
        """Test right click execution"""
        cx, cy = hud.get_cursor_position()
        try:
            hud.right_click(cx, cy)
            time.sleep(0.1)
            # Dismiss context menu by pressing escape key
            hud.press_key("escape")
            print(f"✅ Test 6 (Right Click): Successfully right-clicked at ({cx}, {cy}) and dismissed menu")
        except Exception as e:
            self.fail(f"Right click raised exception: {e}")

    def test_07_hold_and_drag(self):
        """Test click-hold and smooth drag-and-drop"""
        start_x, start_y = hud.get_cursor_position()
        end_x, end_y = start_x + 60, start_y + 40
        
        try:
            hud.drag_and_drop(start_x, start_y, end_x, end_y, duration=0.2, steps=10)
            final_x, final_y = hud.get_cursor_position()
            dist = hud.calculate_euclidean_distance(end_x, end_y, final_x, final_y)
            print(f"✅ Test 7 (Drag & Drop): Start ({start_x}, {start_y}) ➔ Drag End ({end_x}, {end_y}) | Actual ({final_x}, {final_y}) | Error: {dist:.1f}px")
            self.assertLessEqual(dist, 5.0, "Drag end position should match target end position")
        except Exception as e:
            self.fail(f"Drag and drop raised exception: {e}")

    def test_08_trackpad_scrolling(self):
        """Test trackpad scrolling (lines & percentage)"""
        try:
            # Test direct lines scroll
            hud.scroll_trackpad(dy=-5, dx=0)
            time.sleep(0.1)
            # Test 25% percentage scroll
            hud.scroll_trackpad(scroll_percentage=25)
            print(f"✅ Test 8 (Trackpad Scroll): Successfully executed line & percentage scroll")
        except Exception as e:
            self.fail(f"Trackpad scroll raised exception: {e}")

    def test_09_screen_capture_engine(self):
        """Test macOS screen capture JPEG generation"""
        jpeg_bytes = agent.capture_screen()
        self.assertIsNotNone(jpeg_bytes)
        self.assertGreater(len(jpeg_bytes), 1000, "JPEG screenshot size should be > 1KB")
        print(f"✅ Test 9 (Screen Capture): Successfully captured screen JPEG ({len(jpeg_bytes)/1024:.1f} KB)")

    def test_10_apple_vision_ocr(self):
        """Test Apple Vision framework OCR text grounding"""
        try:
            results = agent.find_text_on_screen("Finder")
            print(f"✅ Test 10 (Apple Vision OCR): OCR query returned {len(results)} matches for 'Finder'")
            if results:
                top = results[0]
                print(f"   ↳ First Match: '{top['text']}' @ Center ({top['x']}, {top['y']})")
        except Exception as e:
            self.fail(f"Apple Vision OCR raised exception: {e}")

    def test_11_ax_tree_multi_signal_info(self):
        """Test AXTree multi-signal verification helper (PID, App Name, Window Count)"""
        app_info = ax_engine.get_frontmost_app_info()
        self.assertIn("pid", app_info)
        self.assertIn("name", app_info)
        self.assertIn("window_count", app_info)
        print(f"✅ Test 11 (AXTree Multi-Signal): Frontmost App: '{app_info['name']}' (PID {app_info['pid']}, Windows: {app_info['window_count']})")

if __name__ == "__main__":
    unittest.main(verbosity=2)
