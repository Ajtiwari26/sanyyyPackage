// ==============================================================================
// 🌸 SANYYY MONGOBD LICENSE, OTP AUTH & SID CONTROL BACKEND
// ==============================================================================
// Primary Key: 6-digit SID (e.g. 839201)
// Database: MongoDB Atlas (sanyyy cluster)
// SMTP Email Auth: Gmail App Password
// ==============================================================================

const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const nodemailer = require('nodemailer');

const app = express();
app.use(express.json());
app.use(cors());

// MongoDB Connection URI
const MONGO_URI = process.env.MONGODB_URI || "mongodb+srv://verifysanyyy_db_user:ifiVKYNW2qb7Ga3C@sanyyy.fd9fakj.mongodb.net/?appName=sanyyy";

// Gmail SMTP Credentials
const SMTP_USER = process.env.SMTP_USER || "ajaytiwari2602@gmail.com";
const SMTP_PASS = process.env.SMTP_PASS || "ewtm minb rtwr zidh";

// ------------------------------------------------------------------------------
// MONGOBD DATABASE SETUP
// ------------------------------------------------------------------------------
mongoose.connect(MONGO_URI)
    .then(() => console.log('✅ Connected to MongoDB Atlas (Sanyyy Database)'))
    .catch(err => console.error('❌ MongoDB Connection Error:', err.message));

// User Schema (Primary Key: sid)
const UserSchema = new mongoose.Schema({
    sid: { type: String, required: true, unique: true, index: true }, // 6-digit unique SID (e.g. 839201)
    name: { type: String, required: true },
    email: { type: String, required: true, lowercase: true, trim: true },
    phone: { type: String, required: true },
    hwid: { type: String, required: true },
    status: { type: String, enum: ['active', 'blocked'], default: 'active' },
    otp: { type: String, default: null },
    otpExpires: { type: Date, default: null },
    createdAt: { type: Date, default: Date.now },
    lastActiveAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', UserSchema);

// ------------------------------------------------------------------------------
// SMTP NODEMAILER TRANSPORTER SETUP
// ------------------------------------------------------------------------------
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: SMTP_USER,
        pass: SMTP_PASS
    }
});

// Helper: Generate 6-digit random code
function generate6DigitCode() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// ------------------------------------------------------------------------------
// 1. API: REQUEST OTP FOR EMAIL VERIFICATION
// ------------------------------------------------------------------------------
app.post('/api/v1/auth/request-otp', async (req, res) => {
    try {
        const { name, email, phone, hwid } = req.body;
        if (!email || !phone || !name) {
            return res.status(400).json({ error: 'Name, Email, and Phone number are required.' });
        }

        const otp = generate6DigitCode();
        const otpExpires = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes validity

        // Find existing user by email or phone, or create pending user object
        let user = await User.findOne({ email: email.toLowerCase() });
        if (!user) {
            // Temporary SID until verified
            const tempSid = generate6DigitCode();
            user = new User({
                sid: tempSid,
                name,
                email: email.toLowerCase(),
                phone,
                hwid: hwid || 'PENDING',
                status: 'active',
                otp,
                otpExpires
            });
        } else {
            user.otp = otp;
            user.otpExpires = otpExpires;
            if (name) user.name = name;
            if (phone) user.phone = phone;
            if (hwid) user.hwid = hwid;
        }

        await user.save();

        // Send OTP Email via Nodemailer
        const mailOptions = {
            from: `"Sanyyy AI Assistant" <${SMTP_USER}>`,
            to: email,
            subject: '🌸 Sanyyy Assistant - Your Email Verification Code',
            html: `
                <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f6f9;">
                    <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                        <h2 style="color: #6C5CE7; text-align: center;">🌸 Sanyyy AI Email Verification</h2>
                        <p>Hello <strong>${name}</strong>,</p>
                        <p>Thank you for setting up Sanyyy AI Assistant on your Windows device. Please use the following 6-digit verification code to complete your setup:</p>
                        <div style="text-align: center; margin: 25px 0;">
                            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #00B894; background: #E8F8F5; padding: 10px 20px; border-radius: 8px;">${otp}</span>
                        </div>
                        <p style="color: #888; font-size: 13px; text-align: center;">This code is valid for 10 minutes. If you did not request this code, please ignore this email.</p>
                    </div>
                </div>
            `
        };

        transporter.sendMail(mailOptions, (err, info) => {
            if (err) {
                console.error('❌ Email sending error:', err.message);
                return res.status(500).json({ error: 'Failed to send verification email. Please check your email address.' });
            }
            console.log(`[+] OTP Email sent to ${email}: ${info.response}`);
            res.json({ success: true, message: 'OTP verification code sent to your email.' });
        });

    } catch (e) {
        console.error('Error in /request-otp:', e);
        res.status(500).json({ error: 'Server error requesting OTP.' });
    }
});

// ------------------------------------------------------------------------------
// 2. API: VERIFY OTP & GENERATE FINAL SID
// ------------------------------------------------------------------------------
app.post('/api/v1/auth/verify-otp', async (req, res) => {
    try {
        const { email, otp, hwid } = req.body;
        if (!email || !otp) {
            return res.status(400).json({ error: 'Email and OTP are required.' });
        }

        const user = await User.findOne({ email: email.toLowerCase() });
        if (!user) {
            return res.status(404).json({ error: 'No activation request found for this email.' });
        }

        if (user.otp !== otp || !user.otpExpires || user.otpExpires < new Date()) {
            return res.status(400).json({ error: 'Invalid or expired OTP code.' });
        }

        // Clear OTP once verified
        user.otp = null;
        user.otpExpires = null;
        user.lastActiveAt = new Date();
        if (hwid) user.hwid = hwid;

        // Check if user is blocked
        if (user.status === 'blocked') {
            return res.status(403).json({
                status: 'blocked',
                message: '🛑 You have been blocked by the admin. Contact admin to regain access.'
            });
        }

        await user.save();
        console.log(`[+] USER VERIFIED: SID [${user.sid}] - Email: ${user.email} - HWID: ${user.hwid}`);

        res.json({
            success: true,
            status: 'active',
            sid: user.sid,
            user: { sid: user.sid, name: user.name, email: user.email, phone: user.phone, status: user.status }
        });

    } catch (e) {
        console.error('Error in /verify-otp:', e);
        res.status(500).json({ error: 'Server error verifying OTP.' });
    }
});

// ------------------------------------------------------------------------------
// 3. API: CHECK DEVICE & SID STATUS
// ------------------------------------------------------------------------------
app.get('/api/v1/auth/check-status', async (req, res) => {
    try {
        const { sid, hwid } = req.query;
        if (!sid) {
            return res.status(400).json({ error: 'SID is required.' });
        }

        const user = await User.findOne({ sid });
        if (!user) {
            return res.status(404).json({ status: 'unregistered', message: 'SID not found.' });
        }

        if (user.status === 'blocked') {
            return res.status(403).json({
                status: 'blocked',
                message: '🛑 You have been blocked by the admin. Contact admin to regain access.'
            });
        }

        user.lastActiveAt = new Date();
        if (hwid) user.hwid = hwid;
        await user.save();

        res.json({ status: 'active', sid: user.sid, message: 'User access is active.' });
    } catch (e) {
        res.status(500).json({ error: 'Server error checking status.' });
    }
});

// ------------------------------------------------------------------------------
// 4. ADMIN APIS: CREATE SID, UPDATE SID, REVOKE / GRANT ACCESS
// ------------------------------------------------------------------------------

// Create new SID manually
app.post('/admin/sid/create', async (req, res) => {
    try {
        const { name, email, phone, hwid, status } = req.body;
        const newSid = generate6DigitCode();

        const user = new User({
            sid: newSid,
            name: name || 'Admin Created User',
            email: email ? email.toLowerCase() : `user${newSid}@sanyyy.app`,
            phone: phone || '0000000000',
            hwid: hwid || 'MANUAL-HWID',
            status: status || 'active'
        });

        await user.save();
        res.json({ success: true, sid: newSid, user });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Update Name or Email on existing SID
app.post('/admin/sid/update', async (req, res) => {
    try {
        const { sid, name, email, phone } = req.body;
        const user = await User.findOne({ sid });
        if (!user) return res.status(404).json({ error: 'SID not found.' });

        if (name) user.name = name;
        if (email) user.email = email.toLowerCase();
        if (phone) user.phone = phone;

        await user.save();
        res.json({ success: true, user });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Revoke or Grant Access on SID
app.post('/admin/sid/status', async (req, res) => {
    try {
        const { sid, status } = req.body;
        if (!['active', 'blocked'].includes(status)) {
            return res.status(400).json({ error: 'Status must be active or blocked.' });
        }

        const user = await User.findOne({ sid });
        if (!user) return res.status(404).json({ error: 'SID not found.' });

        user.status = status;
        await user.save();
        console.log(`[!] ADMIN CHANGED SID ${sid} STATUS TO: ${status.toUpperCase()}`);

        res.json({ success: true, user });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ------------------------------------------------------------------------------
// 5. ADMIN WEB CONTROL PANEL
// ------------------------------------------------------------------------------
app.get('/admin', async (req, res) => {
    try {
        const users = await User.find().sort({ createdAt: -1 });
        let rows = '';

        users.forEach(u => {
            const isBlocked = u.status === 'blocked';
            const statusBadge = isBlocked 
                ? `<span style="background: #ff4d4f; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold;">BLOCKED</span>` 
                : `<span style="background: #52c41a; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold;">ACTIVE</span>`;
            
            const actionBtn = isBlocked
                ? `<button onclick="updateSidStatus('${u.sid}', 'active')" style="background: #52c41a; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight: bold;">Grant Access</button>`
                : `<button onclick="updateSidStatus('${u.sid}', 'blocked')" style="background: #ff4d4f; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight: bold;">Revoke Access</button>`;

            rows += `<tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;"><strong style="font-size: 16px; color: #6C5CE7;">${u.sid}</strong></td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;"><strong>${u.name}</strong></td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">${u.email}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">${u.phone}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 11px;">${u.hwid}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">${statusBadge}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; font-size: 12px; color: #666;">${new Date(u.lastActiveAt).toLocaleString()}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">${actionBtn}</td>
            </tr>`;
        });

        if (!rows) {
            rows = `<tr><td colspan="8" style="padding: 20px; text-align: center; color: #999;">No registered Sanyyy users yet in MongoDB.</td></tr>`;
        }

        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sanyyy Admin Control Panel (MongoDB)</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 30px; }
                    .card { background: white; border-radius: 12px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 1200px; margin: 0 auto; }
                    h1 { margin-top: 0; color: #1a1a1a; display: flex; align-items: center; gap: 10px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; text-align: left; }
                    th { background: #fafafa; padding: 12px; border-bottom: 2px solid #e8e8e8; color: #555; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>🌸 Sanyyy AI - MongoDB SID & Access Dashboard</h1>
                    <p style="color: #666;">Manage 6-digit Sanyyy User IDs (SIDs), view verified email users, and revoke or grant access instantly.</p>
                    <table>
                        <thead>
                            <tr>
                                <th>SID (Primary Key)</th>
                                <th>User Name</th>
                                <th>Email Address</th>
                                <th>Phone Number</th>
                                <th>Hardware ID (HWID)</th>
                                <th>Status</th>
                                <th>Last Active</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>

                <script>
                    async function updateSidStatus(sid, status) {
                        if (confirm("Are you sure you want to " + status.toUpperCase() + " access for SID: " + sid + "?")) {
                            const res = await fetch('/admin/sid/status', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ sid, status })
                            });
                            const data = await res.json();
                            if (data.success) {
                                location.reload();
                            } else {
                                alert("Error: " + data.error);
                            }
                        }
                    }
                </script>
            </body>
            </html>
        `);
    } catch (e) {
        res.status(500).send("Error loading admin dashboard.");
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`=======================================================`);
    console.log(`🚀 SANYYY MONGODB LICENSE BACKEND RUNNING ON PORT ${PORT}`);
    console.log(`🌐 Admin Dashboard: http://localhost:${PORT}/admin`);
    console.log(`=======================================================`);
});
