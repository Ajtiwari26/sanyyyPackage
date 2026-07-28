#!/usr/bin/env python3
"""
🌸 SANYYY MULTI-STEP WINDOWS ONBOARDING WIZARD & ACCESS ENFORCER
=================================================================
Step 1: User Identity (Name, Email, Phone) + Email OTP Verification.
Step 2: Gemini API Key Configuration.
Step 3: Device Permissions & Wake Daemon Auto-Start Setup.
Step 4: Unique 6-digit SID Confirmation & Sanyyy Assistant Launch!
"""

import os
import sys
import json
import time
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

# Import local configuration manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_manager

class SanyyyMultiStepWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌸 Sanyyy AI Assistant - Onboarding Wizard")
        self.root.geometry("520x520")
        self.root.resizable(False, False)

        # Center Window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.config = config_manager.load_config()
        self.hwid = config_manager.get_hardware_id()
        self.backend_url = config_manager.get_backend_url()

        self.current_step = 1
        self.verified_sid = self.config.get("sid", None)

        # Header Frame
        self.header_frame = tk.Frame(self.root, bg="#6C5CE7", height=80)
        self.header_frame.pack(fill="x")

        self.title_label = tk.Label(self.header_frame, text="🌸 Sanyyy AI Setup", font=("Segoe UI", 16, "bold"), fg="white", bg="#6C5CE7")
        self.title_label.pack(pady=(12, 0))

        self.step_label = tk.Label(self.header_frame, text="Step 1 of 4: Identity & Email Verification", font=("Segoe UI", 9), fg="#E0DFFF", bg="#6C5CE7")
        self.step_label.pack(pady=(2, 10))

        # Main Body Container Frame
        self.container = tk.Frame(self.root, padx=25, pady=15)
        self.container.pack(fill="both", expand=True)

        self.render_step()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def render_step(self):
        self.clear_container()
        if self.current_step == 1:
            self.render_step_1()
        elif self.current_step == 2:
            self.render_step_2()
        elif self.current_step == 3:
            self.render_step_3()
        elif self.current_step == 4:
            self.render_step_4()

    # --------------------------------------------------------------------------
    # STEP 1: IDENTITY & OTP EMAIL VERIFICATION
    # --------------------------------------------------------------------------
    def render_step_1(self):
        self.step_label.config(text="Step 1 of 4: Identity & Email Verification")

        tk.Label(self.container, text="Full Name:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        self.name_ent = tk.Entry(self.container, font=("Segoe UI", 10), width=45)
        self.name_ent.insert(0, self.config.get("name", ""))
        self.name_ent.pack(pady=(0, 8))

        tk.Label(self.container, text="Email Address (for 6-digit OTP):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        self.email_ent = tk.Entry(self.container, font=("Segoe UI", 10), width=45)
        self.email_ent.insert(0, self.config.get("email", ""))
        self.email_ent.pack(pady=(0, 8))

        tk.Label(self.container, text="Phone Number:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        self.phone_ent = tk.Entry(self.container, font=("Segoe UI", 10), width=45)
        self.phone_ent.insert(0, self.config.get("phone", ""))
        self.phone_ent.pack(pady=(0, 10))

        self.btn_send_otp = tk.Button(
            self.container, text="📩 Send 6-Digit Verification Code to Email",
            font=("Segoe UI", 10, "bold"), bg="#6C5CE7", fg="white",
            relief="flat", cursor="hand2", command=self.send_otp
        )
        self.btn_send_otp.pack(fill="x", ipady=6, pady=(0, 12))

        # OTP Entry section (hidden initially until sent)
        tk.Label(self.container, text="Enter 6-Digit Email OTP Code:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        self.otp_ent = tk.Entry(self.container, font=("Segoe UI", 12, "bold"), width=20, justify="center")
        self.otp_ent.pack(pady=(0, 12))

        self.btn_verify_otp = tk.Button(
            self.container, text="✅ Verify Code & Continue ➡️",
            font=("Segoe UI", 11, "bold"), bg="#00B894", fg="white",
            relief="flat", cursor="hand2", command=self.verify_otp
        )
        self.btn_verify_otp.pack(fill="x", ipady=8)

    def send_otp(self):
        name = self.name_ent.get().strip()
        email = self.email_ent.get().strip()
        phone = self.phone_ent.get().strip()

        if not name or not email or not phone:
            messagebox.showerror("Error", "Please fill in Name, Email, and Phone number.")
            return

        self.btn_send_otp.config(state="disabled", text="⏳ Sending OTP Email...")
        self.root.update()

        try:
            res = requests.post(f"{self.backend_url}/api/v1/auth/request-otp", json={
                "name": name, "email": email, "phone": phone, "hwid": self.hwid
            }, timeout=8)

            if res.status_code == 200:
                messagebox.showinfo("OTP Sent", f"A 6-digit OTP code has been sent to {email}.\nPlease check your inbox/spam folder.")
                self.btn_send_otp.config(text="✓ OTP Sent to Email")
            else:
                err = res.json().get("error", "Failed to send OTP email.")
                messagebox.showerror("Error", err)
                self.btn_send_otp.config(state="normal", text="📩 Resend 6-Digit OTP Code")
        except Exception as e:
            messagebox.showerror("Network Error", f"Could not connect to backend server:\n{e}")
            self.btn_send_otp.config(state="normal", text="📩 Send 6-Digit Verification Code")

    def verify_otp(self):
        email = self.email_ent.get().strip()
        otp = self.otp_ent.get().strip()

        if not email or not otp:
            messagebox.showerror("Error", "Please enter the 6-digit OTP received on your email.")
            return

        try:
            res = requests.post(f"{self.backend_url}/api/v1/auth/verify-otp", json={
                "email": email, "otp": otp, "hwid": self.hwid
            }, timeout=8)

            if res.status_code == 200:
                data = res.json()
                self.verified_sid = data.get("sid")
                self.config.update({
                    "name": self.name_ent.get().strip(),
                    "email": email,
                    "phone": self.phone_ent.get().strip(),
                    "sid": self.verified_sid,
                    "hwid": self.hwid
                })
                config_manager.save_config(self.config)

                messagebox.showinfo("Success", f"🎉 Email Verified Successfully!\nYour assigned Sanyyy ID (SID) is: {self.verified_sid}")
                self.current_step = 2
                self.render_step()
            elif res.status_code == 403:
                messagebox.showerror("Access Blocked", "🛑 You have been blocked by the admin. Contact admin to regain access.")
            else:
                err = res.json().get("error", "Invalid or expired OTP.")
                messagebox.showerror("Error", err)
        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {e}")

    # --------------------------------------------------------------------------
    # STEP 2: GEMINI API KEY SETUP
    # --------------------------------------------------------------------------
    def render_step_2(self):
        self.step_label.config(text="Step 2 of 4: Gemini Live API Key Setup")

        tk.Label(self.container, text="🔑 Gemini API Key Configuration", font=("Segoe UI", 12, "bold"), fg="#6C5CE7").pack(anchor="w", pady=(0, 5))
        tk.Label(self.container, text="Sanyyy uses Google Gemini Live API for real-time voice and desktop interaction.", font=("Segoe UI", 9), fg="#555", wraplength=450, justify="left").pack(anchor="w", pady=(0, 15))

        tk.Label(self.container, text="Enter Your Gemini API Key:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        self.api_ent = tk.Entry(self.container, font=("Segoe UI", 11), width=45, show="*")
        self.api_ent.insert(0, self.config.get("gemini_api_key", ""))
        self.api_ent.pack(pady=(0, 20))

        btn_save_api = tk.Button(
            self.container, text="Save API Key & Continue ➡️",
            font=("Segoe UI", 11, "bold"), bg="#00B894", fg="white",
            relief="flat", cursor="hand2", command=self.save_step_2
        )
        btn_save_api.pack(fill="x", ipady=8)

    def save_step_2(self):
        api_key = self.api_ent.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter a valid Gemini API Key.")
            return

        self.config["gemini_api_key"] = api_key
        config_manager.save_config(self.config)

        self.current_step = 3
        self.render_step()

    # --------------------------------------------------------------------------
    # STEP 3: PERMISSIONS & WAKE DAEMON SETUP
    # --------------------------------------------------------------------------
    def render_step_3(self):
        self.step_label.config(text="Step 3 of 4: Device Permissions & Wake Daemon")

        tk.Label(self.container, text="⚙️ Device Permissions & Listen Daemon", font=("Segoe UI", 12, "bold"), fg="#6C5CE7").pack(anchor="w", pady=(0, 5))
        tk.Label(self.container, text="Enable device capabilities so Sanyyy can respond to wake words and control your desktop:", font=("Segoe UI", 9), fg="#555", wraplength=450, justify="left").pack(anchor="w", pady=(0, 15))

        self.chk_mic_var = tk.BooleanVar(value=True)
        chk_mic = tk.Checkbutton(self.container, text="🎙️ Microphone & Audio Stream Permission", variable=self.chk_mic_var, font=("Segoe UI", 10, "bold"))
        chk_mic.pack(anchor="w", pady=5)

        self.chk_ax_var = tk.BooleanVar(value=True)
        chk_ax = tk.Checkbutton(self.container, text="🖥️ Desktop Vision & Accessibility Automation", variable=self.chk_ax_var, font=("Segoe UI", 10, "bold"))
        chk_ax.pack(anchor="w", pady=5)

        self.chk_daemon_var = tk.BooleanVar(value=True)
        chk_daemon = tk.Checkbutton(self.container, text="👂 Enable Background Wake Daemon ('Hey Sanyyy')", variable=self.chk_daemon_var, font=("Segoe UI", 10, "bold"))
        chk_daemon.pack(anchor="w", pady=5)

        btn_save_permissions = tk.Button(
            self.container, text="Grant Permissions & Complete Setup ➡️",
            font=("Segoe UI", 11, "bold"), bg="#00B894", fg="white",
            relief="flat", cursor="hand2", command=self.save_step_3
        )
        btn_save_permissions.pack(fill="x", ipady=8, pady=(25, 0))

    def save_step_3(self):
        self.config["permissions"] = {
            "microphone": self.chk_mic_var.get(),
            "accessibility": self.chk_ax_var.get(),
            "wake_daemon": self.chk_daemon_var.get()
        }
        config_manager.save_config(self.config)

        self.current_step = 4
        self.render_step()

    # --------------------------------------------------------------------------
    # STEP 4: ONBOARDING COMPLETE & LAUNCH SANYYY
    # --------------------------------------------------------------------------
    def render_step_4(self):
        self.step_label.config(text="Step 4 of 4: Setup Complete!")

        tk.Label(self.container, text="🎉 Sanyyy AI Setup Complete!", font=("Segoe UI", 14, "bold"), fg="#00B894").pack(pady=(10, 5))

        sid_frame = tk.Frame(self.container, bg="#E8F8F5", padx=15, pady=12, relief="groove", bd=1)
        sid_frame.pack(fill="x", pady=15)

        tk.Label(sid_frame, text="Your Assigned Sanyyy User ID (SID):", font=("Segoe UI", 10), bg="#E8F8F5", fg="#333").pack()
        tk.Label(sid_frame, text=f"{self.verified_sid or self.config.get('sid', '839201')}", font=("Segoe UI", 24, "bold"), bg="#E8F8F5", fg="#6C5CE7").pack()

        tk.Label(self.container, text="Your license and hardware ID are linked to this SID.\nYou can now launch Sanyyy AI Assistant!", font=("Segoe UI", 9), fg="#555", justify="center").pack(pady=(0, 20))

        btn_launch_now = tk.Button(
            self.container, text="🚀 Launch Sanyyy Assistant Now",
            font=("Segoe UI", 12, "bold"), bg="#6C5CE7", fg="white",
            relief="flat", cursor="hand2", command=self.launch_sanyyy_agent
        )
        btn_launch_now.pack(fill="x", ipady=10)

    def launch_sanyyy_agent(self):
        os.environ["GEMINI_API_KEY"] = self.config.get("gemini_api_key", "")
        self.root.destroy()

        print("🌸 Launching Sanyyy Voice Agent...")
        base_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        agent_script = os.path.join(base_dir, "scripts", "sanyyy_wake_daemon.py")

        if not os.path.exists(agent_script):
            agent_script = os.path.join(base_dir, "scripts", "gemini_live_agent.py")

        if not os.path.exists(agent_script):
            parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            agent_script = os.path.join(parent_dir, "scripts", "gemini_live_agent.py")

        if os.path.exists(agent_script):
            subprocess.run([sys.executable, agent_script])

if __name__ == "__main__":
    wizard = SanyyyMultiStepWizard()
    wizard.root.mainloop()
