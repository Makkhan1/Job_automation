const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const axios = require('axios');
const cron = require('node-cron'); // 1. Added cron import

const app = express();
app.use(express.json());

// --- CONFIGURATION ---
const ALLOWED_INCOMING_IDS = [
    '120363310312543689@newsletter', '120363190851267320@newsletter',
    '22879357903024@lid', '919508166407@c.us', '120363227594252483@newsletter'
];
const MY_CHANNEL_ID = '120363425158838403@newsletter';
const FASTAPI_WEBHOOK = process.env.FASTAPI_WEBHOOK || 'http://localhost:8000/webhook/job';

// --- INITIALIZE WHATSAPP CLIENT ---
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './.wwebjs_auth' }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-dev-shm-usage', 
            '--disable-gpu',
            '--no-zygote'
        ]
    }
});

client.on('qr', (qr) => {
    console.log('\n📱 Scan this QR code in WhatsApp to log in:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ WhatsApp Bot is Ready and Connected!');
});

client.on('message', async (msg) => {
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
            console.log(`✅ Forwarded from ${senderName} to FastAPI Core.`);
        } catch (error) {
            console.error('❌ Failed to forward to FastAPI:', error.message);
        }
    }
});

app.post('/send', async (req, res) => {
    const { text } = req.body;
    if (!text) return res.status(400).send({ error: "Text is required" });

    try {
        const channel = await client.getChatById(MY_CHANNEL_ID);
        await channel.sendMessage(text);
        res.status(200).send({ status: 'sent' });
    } catch (error) {
        res.status(500).send({ error: error.toString() });
    }
});

// --- 2. THE 3-HOUR RESTART LOGIC ---
// This runs at minute 0, every 3rd hour (e.g., 12:00, 3:00, 6:00...)
cron.schedule('0 */3 * * *', async () => {
    console.log('\n🔄 CRON TRIGGERED: Refreshing Puppeteer to prevent Detached Frame issue...');
    try {
        await client.destroy(); // Properly close the browser
    } catch (e) {
        console.log("Forcing exit...");
    } finally {
        process.exit(0); // PM2 will automatically restart this process
    }
});

client.initialize();
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🌐 Node API listening on port ${PORT}`));