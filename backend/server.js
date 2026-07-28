// ==============================================================================
// 🌸 SANYYY MONGOBD LICENSE, OTP AUTH & SID CONTROL BACKEND
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
const SMTP_USER = process.env.SMTP_USER || "verify.sanyyy@gmail.com";
const SMTP_PASS = process.env.SMTP_PASS || "rnthkmnzziilbovm";

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
// OFFICIAL GOOGLE GMAIL SMTP TRANSPORTER (verify.sanyyy@gmail.com)
// ------------------------------------------------------------------------------
const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true, // Port 465 SSL connection
    auth: {
        user: SMTP_USER,
        pass: SMTP_PASS
    },
    tls: {
        rejectUnauthorized: false
    }
});

// Send OTP email via Google Gmail SMTP
async function sendVerificationEmail(toEmail, toName, otp) {
    const htmlContent = `
        <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f6f9;">
            <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                <h2 style="color: #6C5CE7; text-align: center;">🌸 Sanyyy AI Email Verification</h2>
                <p>Hello <strong>${escapeAttr(toName)}</strong>,</p>
                <p>Thank you for setting up Sanyyy AI Assistant on your Windows device. Please use the following 6-digit verification code to complete your setup:</p>
                <div style="text-align: center; margin: 25px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #00B894; background: #E8F8F5; padding: 10px 20px; border-radius: 8px;">${otp}</span>
                </div>
                <p style="color: #888; font-size: 13px; text-align: center;">This code is valid for 10 minutes. If you did not request this code, please ignore this email.</p>
            </div>
        </div>
    `;

    return new Promise((resolve) => {
        transporter.sendMail({
            from: `"Sanyyy AI Assistant" <${SMTP_USER}>`,
            to: toEmail,
            subject: '🌸 Sanyyy Assistant - Your Email Verification Code',
            html: htmlContent
        }, (err, info) => {
            if (err) {
                console.error('❌ Official Gmail SMTP error:', err.message);
                resolve(false);
            } else {
                console.log(`[+] Sent OTP via Official Gmail SMTP to ${toEmail}: ${info.response}`);
                resolve(true);
            }
        });
    });
}

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
        const otpExpires = new Date(Date.now() + 10 * 60 * 1000);

        let user = await User.findOne({ email: email.toLowerCase() });
        if (!user) {
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

        const sent = await sendVerificationEmail(email.toLowerCase(), name, otp);
        if (sent) {
            res.json({ success: true, message: 'OTP verification code sent to your email.' });
        } else {
            res.status(500).json({ error: 'Failed to send verification email. Please check your email address.' });
        }

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
            return res.status(404).json({ error: 'User registration record not found. Please request a new OTP.' });
        }

        if (user.status === 'blocked') {
            return res.status(403).json({ error: 'Access blocked by administrator.' });
        }

        if (!user.otp || user.otp !== otp) {
            return res.status(400).json({ error: 'Invalid verification code. Please check your email and try again.' });
        }

        if (user.otpExpires && new Date() > user.otpExpires) {
            return res.status(400).json({ error: 'Verification code has expired. Please request a new OTP.' });
        }

        user.otp = null;
        user.otpExpires = null;
        user.lastActiveAt = new Date();
        if (hwid) user.hwid = hwid;
        await user.save();

        res.json({
            success: true,
            sid: user.sid,
            name: user.name,
            email: user.email,
            message: 'Email verified successfully! Sanyyy Assistant access granted.'
        });

    } catch (e) {
        console.error('Error in /verify-otp:', e);
        res.status(500).json({ error: 'Server error verifying OTP.' });
    }
});

// ------------------------------------------------------------------------------
// 3. API: CHECK DEVICE PERMISSION / BLOCK STATUS (Every Wake Daemon Launch)
// ------------------------------------------------------------------------------
app.post('/api/v1/auth/check-access', async (req, res) => {
    try {
        const { sid, hwid } = req.body;
        if (!sid) {
            return res.status(400).json({ error: 'SID is required.' });
        }

        const user = await User.findOne({ sid });
        if (!user) {
            return res.status(404).json({ allowed: false, reason: 'SID not found.' });
        }

        if (user.status === 'blocked') {
            return res.status(403).json({ allowed: false, reason: 'Access blocked by administrator.' });
        }

        user.lastActiveAt = new Date();
        await user.save();

        res.json({
            allowed: true,
            sid: user.sid,
            name: user.name,
            email: user.email,
            status: user.status
        });

    } catch (e) {
        console.error('Error in /check-access:', e);
        res.status(500).json({ error: 'Server error checking access status.' });
    }
});

// ------------------------------------------------------------------------------
// 4. ADMIN DASHBOARD & LIVE USER CONTROL
// ------------------------------------------------------------------------------
app.get('/api/admin/users', async (req, res) => {
    try {
        const users = await User.find().sort({ createdAt: -1 });
        res.json({ success: true, users });
    } catch (e) {
        res.status(500).json({ error: 'Failed to fetch user database.' });
    }
});

app.post('/api/admin/toggle-block', async (req, res) => {
    try {
        const { sid, action } = req.body;
        const user = await User.findOne({ sid });
        if (!user) return res.status(404).json({ error: 'User not found.' });

        user.status = action === 'block' ? 'blocked' : 'active';
        await user.save();

        res.json({ success: true, user });
    } catch (e) {
        res.status(500).json({ error: 'Failed to update user status.' });
    }
});

app.get('/admin', async (req, res) => {
    try {
        const users = await User.find().sort({ createdAt: -1 });
        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>🌸 Sanyyy AI Admin Dashboard</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 30px; }
                    .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
                    h1 { color: #6C5CE7; margin-top: 0; display: flex; align-items: center; justify-content: space-between; }
                    .badge { background: #6C5CE7; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
                    th { background-color: #f8f9fa; color: #444; font-weight: 600; }
                    tr:hover { background-color: #fcfcfc; }
                    .status-active { color: #00B894; font-weight: bold; }
                    .status-blocked { color: #D63031; font-weight: bold; }
                    .btn-block { background: #D63031; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; }
                    .btn-unblock { background: #00B894; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; }
                    .btn-block:hover { background: #ff7675; }
                    .btn-unblock:hover { background: #55efc4; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🌸 Sanyyy AI License & User Control Panel <span class="badge">${users.length} Users</span></h1>
                    <table>
                        <thead>
                            <tr>
                                <th>SID</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>HWID</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map(u => `
                                <tr>
                                    <td><strong>${u.sid}</strong></td>
                                    <td>${escapeAttr(u.name)}</td>
                                    <td>${escapeAttr(u.email)}</td>
                                    <td>${escapeAttr(u.phone)}</td>
                                    <td><code style="font-size:11px; background:#eee; padding:2px 4px; border-radius:4px;">${escapeAttr(u.hwid)}</code></td>
                                    <td class="status-${u.status}">${u.status.toUpperCase()}</td>
                                    <td>
                                        <button class="${u.status === 'active' ? 'btn-block' : 'btn-unblock'}" onclick="toggleBlock('${u.sid}', '${u.status === 'active' ? 'block' : 'unblock'}')">
                                            ${u.status === 'active' ? '🚫 Block' : '✅ Unblock'}
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <script>
                    async function toggleBlock(sid, action) {
                        if (confirm(\`Are you sure you want to \${action} user SID \${sid}?\`)) {
                            const res = await fetch('/api/admin/toggle-block', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ sid, action })
                            });
                            if (res.ok) window.location.reload();
                        }
                    }
                    setTimeout(() => window.location.reload(), 15000);
                </script>
            </body>
            </html>
        `);
    } catch (e) {
        res.status(500).send('Error rendering admin dashboard.');
    }
});

const PORT = process.env.PORT || 3000;
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`=======================================================`);
        console.log(`🚀 SANYYY MONGODB LICENSE BACKEND RUNNING ON PORT ${PORT}`);
        console.log(`🌐 Admin Dashboard: http://localhost:${PORT}/admin`);
        console.log(`=======================================================`);
    });
}

module.exports = app;
