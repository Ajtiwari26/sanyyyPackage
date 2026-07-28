#!/usr/bin/env python3
"""
SANYYY WINDOWS EXECUTABLE PACKAGER
Uses PyInstaller to bundle Python runtime, PyAudio, sounddevice, google-genai,
Tkinter GUI launcher, and Sanyyy scripts into a standalone Windows directory.
"""

import os
import sys
import subprocess

# Ensure UTF-8 output encoding on Windows PowerShell/CMD
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_pyinstaller():
    print("=======================================================")
    print("SANYYY WINDOWS EXE BUILDER (PyInstaller)")
    print("=======================================================")

    builder_dir = os.path.dirname(os.path.abspath(__file__))
    package_dir = os.path.dirname(builder_dir)
    client_script = os.path.join(package_dir, "client", "sanyyy_gui_launcher.py")

    if not os.path.exists(client_script):
        print(f"[!] Error: Client launcher script not found at {client_script}")
        sys.exit(1)

    # Locate scripts directory (inside package_dir/scripts or parent fallback)
    scripts_dir = os.path.join(package_dir, "scripts")
    if not os.path.exists(scripts_dir):
        project_root = os.path.dirname(package_dir)
        scripts_dir = os.path.join(project_root, "scripts")

    print(f"[+] Using Client Script: {client_script}")
    print(f"[+] Using Scripts Directory: {scripts_dir}")

    if not os.path.exists(scripts_dir):
        print(f"[!] ERROR: Scripts directory does not exist at {scripts_dir}")
        sys.exit(1)

    # PyInstaller Arguments
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",                       # Output directory bundle
        "--windowed",                     # Hide console window
        "--name", "Sanyyy",
        "--distpath", os.path.join(package_dir, "dist"),
        "--workpath", os.path.join(package_dir, "build"),
        f"--add-data={scripts_dir}{os.pathsep}scripts",
        f"--add-data={os.path.join(package_dir, 'client')}{os.pathsep}client",
        client_script
    ]

    print(f"[+] Executing Build Command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print("\nSUCCESS! Windows executable built successfully under:")
        print(f"Directory: {os.path.join(package_dir, 'dist', 'Sanyyy')}")
    except subprocess.CalledProcessError as e:
        print(f"\nBUILD FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pyinstaller()
