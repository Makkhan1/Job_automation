const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
const { Client, RemoteAuth } = require('whatsapp-web.js');
const { MongoStore } = require('wwebjs-mongo');
const mongoose = require('mongoose');
const qrcode = require('qrcode-terminal');
const express = require('express');
const axios = require('axios');
const cron = require('node-cron');

const app = express();
app.use(express.json());

// --- CONFIGURATION ---
const ALLOWED_INCOMING_IDS = [
    '120363310312543689@newsletter', // Saksham
    '120363190851267320@newsletter', // Vishal
    '22879357903024@lid',            // mahtab
    '919508166407@c.us',
    '120363227594252483@newsletter'  // Rounak
];
const MY_CHANNEL_ID = '120363425158838403@newsletter'; 
// NOTE: Change localhost to your actual FastAPI Render URL when deploying the backend!
const FASTAPI_WEBHOOK = process.env.FASTAPI_WEBHOOK || 'http://localhost:8000/webhook/job';

console.log('⏳ Connecting to MongoDB...');

// --- 1. CONNECT TO MONGODB FIRST ---
mongoose.connect(process.env.MONGODB_URI).then(() => {
    console.log('✅ Connected to MongoDB Atlas');
    
    // Initialize the MongoDB Store for WhatsApp Auth
    const store = new MongoStore({ mongoose: mongoose });

    // --- 2. INITIALIZE WHATSAPP CLIENT ---
    const client = new Client({
        authStrategy: new RemoteAuth({
            clientId: 'job-bot-session',
            store: store,
            backupSyncIntervalMs: 300000 // Backs up sync state every 5 minutes
        }),
        puppeteer: {
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        }
    });

    // --- WHATSAPP EVENTS ---
    client.on('qr', (qr) => {
        console.log('\n📱 Scan this QR code in WhatsApp to log in for the FIRST time:');
        qrcode.generate(qr, { small: true });
    });

    client.on('remote_session_saved', () => {
        console.log('💾 WhatsApp Session successfully synced to MongoDB!');
    });

    client.on('ready', () => {
        console.log('✅ WhatsApp Bot is Ready and Connected!');
    });

    client.on('message', async (msg) => {
        // Safe ID Grabber
        try {
            let chatName = msg.from.includes('@newsletter') ? "WhatsApp Channel" : (await msg.getChat()).name;
            console.log(`\n--- NEW MESSAGE DETECTED ---`);
            console.log(`Chat Name  : ${chatName}`);
            console.log(`ID TO COPY : ${msg.from}`);
            console.log(`Preview    : ${msg.body.substring(0, 60)}...\n`);
        } catch (error) {}

        // Forward to FastAPI
        if (ALLOWED_INCOMING_IDS.includes(msg.from)) {
            try {
                let senderName = "WhatsApp Channel";
                let sourceType = "Channel";

                if (!msg.from.includes('@newsletter')) {
                    const contact = await msg.getContact();
                    senderName = contact.name || contact.pushname || msg.from;
                    sourceType = msg.from.includes('@g.us') ? 'Group' : 'Contact';
                }

                await axios.post(FASTAPI_WEBHOOK, {
                    source_type: sourceType,
                    platform: 'WhatsApp',
                    sender_name: senderName,
                    raw_text: msg.body
                });
                console.log('✅ Forwarded to FastAPI Core.');
            } catch (error) {
                console.error('❌ Failed to forward to FastAPI:', error.message);
            }
        }
    });

    // --- EXPRESS ENDPOINTS ---
    app.post('/send', async (req, res) => {
        const { text } = req.body;
        if (!text) return res.status(400).send({ error: "Text is required" });

        try {
            const channel = await client.getChatById(MY_CHANNEL_ID);
            await channel.sendMessage(text);
            console.log('🚀 Successfully posted to WhatsApp Channel!');
            res.status(200).send({ status: 'sent' });
        } catch (error) {
            console.error('❌ Failed to send WhatsApp message:', error);
            res.status(500).send({ error: error.toString() });
        }
    });

    app.get('/ping', (req, res) => {
        console.log('🏓 Ping received! Keeping server awake.');
        res.status(200).send('WhatsApp Bot is awake!');
    });

    // --- START EVERYTHING ---
    client.initialize();
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
        console.log(`🌐 Node API listening on port ${PORT}`);
    });

    // --- 3-HOUR AUTO RESTART (Prevents Detached Frame Crash) ---
    cron.schedule('0 */3 * * *', async () => {
        console.log('\n🔄 CRON TRIGGERED: Performing scheduled 3-hour restart to prevent Puppeteer memory leak...');
        try {
            await client.destroy();
        } catch (error) {} 
        finally {
            console.log('Exiting... Render will immediately restart the server.');
            process.exit(0); 
        }
    });

}).catch(err => {
    console.error('❌ Failed to connect to MongoDB. Check your connection string!', err);
});