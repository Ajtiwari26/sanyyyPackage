// ==============================================================================
// 🌸 SANYYY MONGODB LICENSE, OTP AUTH & SID CONTROL BACKEND
// ==============================================================================
// Primary Key: 6-digit SID (e.g. 839201)
// Database: MongoDB Atlas (sanyyy cluster)
// SMTP Email Auth: Gmail App Password
// Real-Time Admin Dashboard with Auto-Refresh
// ==============================================================================

require('dotenv').config();

const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const nodemailer = require('nodemailer');

const app = express();
app.use(express.json());
app.use(cors());

// Environment Variables (Loaded from process.env or .env file)
const MONGO_URI = process.env.MONGODB_URI || "mongodb+srv://verifysanyyy_db_user:ifiVKYNW2qb7Ga3C@sanyyy.fd9fakj.mongodb.net/?appName=sanyyy";
const SMTP_USER = process.env.SMTP_USER || "ajaytiwari2602@gmail.com";
const SMTP_PASS = process.env.SMTP_PASS || "ewtm minb rtwr zidh";

if (!MONGO_URI) {
    console.error("❌ ERROR: MONGODB_URI environment variable is missing!");
}

// ------------------------------------------------------------------------------
// HEALTH CHECK ENDPOINT
// ------------------------------------------------------------------------------
app.get(['/health', '/api/health'], (req, res) => {
    const dbState = mongoose.connection.readyState === 1 ? 'connected' : 'disconnected';
    res.json({
        status: 'ok',
        service: 'sanyyy-backend',
        database: dbState,
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
    });
});

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

// Helper: Escape HTML entity attributes
function escapeAttr(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ------------------------------------------------------------------------------
// 1. API: REQUEST OTP FOR EMAIL VERIFICATION (Initial Setup on Windows Installation)
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
            // Temporary 6-digit SID until verified
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
        console.log(`[+] NEW USER SETUP INITIATED ON WINDOWS: ${name} (${email}) - SID: ${user.sid}`);

        // Send OTP Email via Nodemailer
        const mailOptions = {
            from: `"Sanyyy AI Assistant" <${SMTP_USER}>`,
            to: email,
            subject: '🌸 Sanyyy Assistant - Your Email Verification Code',
            html: `
                <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f6f9;">
                    <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                        <h2 style="color: #6C5CE7; text-align: center;">🌸 Sanyyy AI Email Verification</h2>
                        <p>Hello <strong>${escapeAttr(name)}</strong>,</p>
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
// 2. API: VERIFY OTP & CONFIRM FINAL SID
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
        console.log(`[+] USER VERIFIED ON WINDOWS PC: SID [${user.sid}] - Email: ${user.email} - HWID: ${user.hwid}`);

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
// 4. ADMIN APIS: CREATE SID, UPDATE SID, DELETE SID, REVOKE / GRANT ACCESS
// ------------------------------------------------------------------------------

// Create new SID manually
app.post('/admin/sid/create', async (req, res) => {
    try {
        const { name, email, phone, hwid, status } = req.body;
        if (!name || !email || !phone) {
            return res.status(400).json({ error: 'Name, Email, and Phone number are required.' });
        }

        const newSid = generate6DigitCode();
        const user = new User({
            sid: newSid,
            name,
            email: email.toLowerCase(),
            phone,
            hwid: hwid || 'MANUAL-HWID',
            status: status || 'active'
        });

        await user.save();
        res.json({ success: true, sid: newSid, user });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Update Name, Email, Phone, or HWID on existing SID
app.post('/admin/sid/update', async (req, res) => {
    try {
        const { sid, name, email, phone, hwid } = req.body;
        if (!sid) return res.status(400).json({ error: 'SID is required.' });

        const user = await User.findOne({ sid });
        if (!user) return res.status(404).json({ error: 'SID not found.' });

        if (name) user.name = name;
        if (email) user.email = email.toLowerCase();
        if (phone) user.phone = phone;
        if (hwid) user.hwid = hwid;

        await user.save();
        res.json({ success: true, user });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Delete SID record from MongoDB Atlas
app.post('/admin/sid/delete', async (req, res) => {
    try {
        const { sid } = req.body;
        if (!sid) return res.status(400).json({ error: 'SID is required.' });

        const result = await User.deleteOne({ sid });
        if (result.deletedCount === 0) {
            return res.status(404).json({ error: 'SID not found in database.' });
        }

        console.log(`[!] ADMIN DELETED SID: ${sid}`);
        res.json({ success: true, message: `SID ${sid} permanently deleted.` });
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

// JSON API endpoint for Real-Time Auto Refresh Dashboard
app.get('/api/admin/users', async (req, res) => {
    try {
        const users = await User.find().sort({ createdAt: -1 });
        res.json({ success: true, users });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ------------------------------------------------------------------------------
// 5. INTERACTIVE REAL-TIME ADMIN WEB CONTROL PANEL
// ------------------------------------------------------------------------------
app.get('/admin', async (req, res) => {
    try {
        const users = await User.find().sort({ createdAt: -1 });
        let rows = '';

        users.forEach(u => {
            const isBlocked = u.status === 'blocked';
            const statusBadge = isBlocked 
                ? `<span style="background: #ff4d4f; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">BLOCKED</span>` 
                : `<span style="background: #52c41a; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">ACTIVE</span>`;
            
            const targetStatus = isBlocked ? 'active' : 'blocked';
            const statusBtnText = isBlocked ? 'Unblock' : 'Block';
            const statusBtnBg = isBlocked ? '#52c41a' : '#fa8c16';

            rows += `<tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;"><strong style="font-size: 16px; color: #6C5CE7; font-family: monospace;">${escapeAttr(u.sid)}</strong></td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;"><strong>${escapeAttr(u.name)}</strong></td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">${escapeAttr(u.email)}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">${escapeAttr(u.phone)}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 11px; color: #555;">${escapeAttr(u.hwid)}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">${statusBadge}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; font-size: 12px; color: #666;">${new Date(u.lastActiveAt).toLocaleString()}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; white-space: nowrap;">
                    <button class="btn-edit" 
                        data-sid="${escapeAttr(u.sid)}" 
                        data-name="${escapeAttr(u.name)}" 
                        data-email="${escapeAttr(u.email)}" 
                        data-phone="${escapeAttr(u.phone)}" 
                        data-hwid="${escapeAttr(u.hwid)}"
                        style="background: #1890ff; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; margin-right: 4px;">Edit</button>

                    <button class="btn-status" 
                        data-sid="${escapeAttr(u.sid)}" 
                        data-status="${targetStatus}"
                        style="background: ${statusBtnBg}; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; margin-right: 4px;">${statusBtnText}</button>

                    <button class="btn-delete" 
                        data-sid="${escapeAttr(u.sid)}"
                        style="background: #ff4d4f; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold;">Delete</button>
                </td>
            </tr>`;
        });

        if (!rows) {
            rows = `<tr><td colspan="8" style="padding: 25px; text-align: center; color: #999;">No registered Sanyyy users found in MongoDB. Use the form above or install Sanyyy on Windows to create a user!</td></tr>`;
        }

        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sanyyy Admin Dashboard - Real-Time User Directory</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 30px; }
                    .card { background: white; border-radius: 12px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 1250px; margin: 0 auto 25px auto; }
                    h1 { margin-top: 0; color: #1a1a1a; display: flex; align-items: center; justify-content: space-between; font-size: 22px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 15px; text-align: left; }
                    th { background: #fafafa; padding: 12px; border-bottom: 2px solid #e8e8e8; color: #555; font-size: 13px; }
                    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 15px; }
                    input { padding: 10px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 14px; width: 100%; box-sizing: border-box; }
                    button.btn-primary { background: #6C5CE7; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; }
                    button.btn-primary:hover { background: #5b4cc4; }
                    
                    /* Live Indicator Badge */
                    .pulse-badge { display: inline-flex; align-items: center; gap: 6px; background: #E8F8F5; color: #00B894; font-size: 12px; font-weight: bold; padding: 4px 12px; border-radius: 20px; border: 1px solid #B2EBF2; }
                    .pulse-dot { width: 8px; height: 8px; background: #00B894; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
                    @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }

                    /* Edit Modal Styling */
                    .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
                    .modal-content { background: white; padding: 25px; border-radius: 10px; width: 450px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
                </style>
            </head>
            <body>
                <!-- Top Card: Add New Sanyyy User ID -->
                <div class="card">
                    <h1>
                        <span>➕ Create / Add New Sanyyy User ID (SID)</span>
                        <span class="pulse-badge"><span class="pulse-dot"></span> Live Sync Active (Auto-Refresh 10s)</span>
                    </h1>
                    <p style="color: #666; margin-bottom: 10px; font-size: 13px;">Manually create a new 6-digit Sanyyy ID linked to a user's Name, Email, and Phone Number.</p>
                    <form id="createForm">
                        <div class="form-grid">
                            <input type="text" id="newName" placeholder="User Full Name" required />
                            <input type="email" id="newEmail" placeholder="Email Address" required />
                            <input type="text" id="newPhone" placeholder="Phone Number" required />
                            <input type="text" id="newHwid" placeholder="Hardware ID (Optional)" />
                            <button type="submit" class="btn-primary">Generate 6-Digit SID</button>
                        </div>
                    </form>
                </div>

                <!-- Main Table Card: All Users -->
                <div class="card">
                    <h1>🌸 Sanyyy AI - Live MongoDB SID Directory</h1>
                    <p style="color: #666; font-size: 13px;">View and edit user details, toggle access (Block / Unblock), or delete SIDs permanently. New Windows installations appear here automatically!</p>
                    <table>
                        <thead>
                            <tr>
                                <th>SID (Primary Key)</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Hardware ID (HWID)</th>
                                <th>Status</th>
                                <th>Last Active</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="userTableBody">
                            ${rows}
                        </tbody>
                    </table>
                </div>

                <!-- Edit User Details Modal Popup -->
                <div id="editModal" class="modal">
                    <div class="modal-content">
                        <h2 style="margin-top: 0; color: #6C5CE7;">✏️ Edit User Details</h2>
                        <input type="hidden" id="editSid" />
                        <div style="margin-bottom: 12px;">
                            <label style="font-size: 12px; font-weight: bold; color: #555;">Full Name:</label>
                            <input type="text" id="editName" style="margin-top: 4px;" />
                        </div>
                        <div style="margin-bottom: 12px;">
                            <label style="font-size: 12px; font-weight: bold; color: #555;">Email Address:</label>
                            <input type="email" id="editEmail" style="margin-top: 4px;" />
                        </div>
                        <div style="margin-bottom: 12px;">
                            <label style="font-size: 12px; font-weight: bold; color: #555;">Phone Number:</label>
                            <input type="text" id="editPhone" style="margin-top: 4px;" />
                        </div>
                        <div style="margin-bottom: 20px;">
                            <label style="font-size: 12px; font-weight: bold; color: #555;">Hardware ID (HWID):</label>
                            <input type="text" id="editHwid" style="margin-top: 4px;" />
                        </div>
                        <div style="text-align: right; gap: 10px; display: flex; justify-content: flex-end;">
                            <button type="button" id="btnCancelModal" style="background: #ccc; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">Cancel</button>
                            <button type="button" id="btnSaveModal" class="btn-primary">Save Changes</button>
                        </div>
                    </div>
                </div>

                <script>
                    document.addEventListener('DOMContentLoaded', () => {
                        // Automatic Background Live Sync (Refreshes user table every 10 seconds)
                        setInterval(async () => {
                            // Don't auto-refresh if modal is open
                            if (document.getElementById('editModal').style.display === 'flex') return;
                            try {
                                const res = await fetch('/api/admin/users');
                                const data = await res.json();
                                if (data.success && data.users) {
                                    renderTableRows(data.users);
                                }
                            } catch (e) {
                                console.warn("Live sync ping error:", e);
                            }
                        }, 10000);

                        function renderTableRows(users) {
                            const tableBody = document.getElementById('userTableBody');
                            if (!users || users.length === 0) {
                                tableBody.innerHTML = '<tr><td colspan="8" style="padding: 25px; text-align: center; color: #999;">No registered Sanyyy users found in MongoDB. Use the form above or install Sanyyy on Windows to create a user!</td></tr>';
                                return;
                            }

                            let html = '';
                            users.forEach(u => {
                                const isBlocked = u.status === 'blocked';
                                const statusBadge = isBlocked 
                                    ? '<span style="background: #ff4d4f; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">BLOCKED</span>' 
                                    : '<span style="background: #52c41a; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">ACTIVE</span>';
                                
                                const targetStatus = isBlocked ? 'active' : 'blocked';
                                const statusBtnText = isBlocked ? 'Unblock' : 'Block';
                                const statusBtnBg = isBlocked ? '#52c41a' : '#fa8c16';

                                html += '<tr>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee;"><strong style="font-size: 16px; color: #6C5CE7; font-family: monospace;">' + escapeHtml(u.sid) + '</strong></td>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee;"><strong>' + escapeHtml(u.name) + '</strong></td>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee;">' + escapeHtml(u.email) + '</td>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee;">' + escapeHtml(u.phone) + '</td>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 11px; color: #555;">' + escapeHtml(u.hwid) + '</td>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee;">' + statusBadge + '</td>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee; font-size: 12px; color: #666;">' + new Date(u.lastActiveAt).toLocaleString() + '</td>' +
                                    '<td style="padding: 12px; border-bottom: 1px solid #eee; white-space: nowrap;">' +
                                        '<button class="btn-edit" data-sid="' + escapeHtml(u.sid) + '" data-name="' + escapeHtml(u.name) + '" data-email="' + escapeHtml(u.email) + '" data-phone="' + escapeHtml(u.phone) + '" data-hwid="' + escapeHtml(u.hwid) + '" style="background: #1890ff; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; margin-right: 4px;">Edit</button>' +
                                        '<button class="btn-status" data-sid="' + escapeHtml(u.sid) + '" data-status="' + targetStatus + '" style="background: ' + statusBtnBg + '; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; margin-right: 4px;">' + statusBtnText + '</button>' +
                                        '<button class="btn-delete" data-sid="' + escapeHtml(u.sid) + '" style="background: #ff4d4f; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold;">Delete</button>' +
                                    '</td>' +
                                '</tr>';
                            });

                            tableBody.innerHTML = html;
                        }

                        function escapeHtml(str) {
                            if (!str) return '';
                            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                        }

                        // Create New SID Handler
                        const createForm = document.getElementById('createForm');
                        createForm.addEventListener('submit', async (e) => {
                            e.preventDefault();
                            const name = document.getElementById('newName').value.trim();
                            const email = document.getElementById('newEmail').value.trim();
                            const phone = document.getElementById('newPhone').value.trim();
                            const hwid = document.getElementById('newHwid').value.trim();

                            try {
                                const res = await fetch('/admin/sid/create', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ name, email, phone, hwid })
                                });
                                const data = await res.json();
                                if (data.success) {
                                    alert("🎉 Success! New 6-Digit SID Created: " + data.sid);
                                    location.reload();
                                } else {
                                    alert("Error: " + (data.error || "Failed to create SID"));
                                }
                            } catch (err) {
                                alert("Network error: " + err.message);
                            }
                        });

                        // Event Delegation for Table Action Buttons
                        const tableBody = document.getElementById('userTableBody');
                        tableBody.addEventListener('click', async (e) => {
                            const target = e.target;
                            
                            // 1. Edit Button
                            if (target.classList.contains('btn-edit')) {
                                const sid = target.getAttribute('data-sid');
                                const name = target.getAttribute('data-name');
                                const email = target.getAttribute('data-email');
                                const phone = target.getAttribute('data-phone');
                                const hwid = target.getAttribute('data-hwid');

                                document.getElementById('editSid').value = sid;
                                document.getElementById('editName').value = name;
                                document.getElementById('editEmail').value = email;
                                document.getElementById('editPhone').value = phone;
                                document.getElementById('editHwid').value = hwid;
                                document.getElementById('editModal').style.display = 'flex';
                            }

                            // 2. Block / Unblock Status Button
                            if (target.classList.contains('btn-status')) {
                                const sid = target.getAttribute('data-sid');
                                const status = target.getAttribute('data-status');
                                if (confirm("Change access status for SID " + sid + " to " + status.toUpperCase() + "?")) {
                                    try {
                                        const res = await fetch('/admin/sid/status', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ sid, status })
                                        });
                                        const data = await res.json();
                                        if (data.success) location.reload();
                                        else alert("Error: " + data.error);
                                    } catch (err) {
                                        alert("Network error: " + err.message);
                                    }
                                }
                            }

                            // 3. Delete Button
                            if (target.classList.contains('btn-delete')) {
                                const sid = target.getAttribute('data-sid');
                                if (confirm("⚠️ PERMANENT DELETE\n\nAre you sure you want to permanently delete SID " + sid + " from MongoDB?")) {
                                    try {
                                        const res = await fetch('/admin/sid/delete', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ sid })
                                        });
                                        const data = await res.json();
                                        if (data.success) location.reload();
                                        else alert("Error: " + data.error);
                                    } catch (err) {
                                        alert("Network error: " + err.message);
                                    }
                                }
                            }
                        });

                        // Modal Save & Cancel Buttons
                        document.getElementById('btnCancelModal').addEventListener('click', () => {
                            document.getElementById('editModal').style.display = 'none';
                        });

                        document.getElementById('btnSaveModal').addEventListener('click', async () => {
                            const sid = document.getElementById('editSid').value;
                            const name = document.getElementById('editName').value.trim();
                            const email = document.getElementById('editEmail').value.trim();
                            const phone = document.getElementById('editPhone').value.trim();
                            const hwid = document.getElementById('editHwid').value.trim();

                            try {
                                const res = await fetch('/admin/sid/update', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ sid, name, email, phone, hwid })
                                });
                                const data = await res.json();
                                if (data.success) {
                                    document.getElementById('editModal').style.display = 'none';
                                    location.reload();
                                } else {
                                    alert("Error: " + data.error);
                                }
                            } catch (err) {
                                alert("Network error: " + err.message);
                            }
                        });
                    });
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
