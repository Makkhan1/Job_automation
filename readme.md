# 🚀 Automated Job Pipeline

## 📋 Overview
This project is an automated, high-performance cloud pipeline designed to scrape job postings from Telegram channels, process and format them using an LLM (Groq 120B), and instantly broadcast them to a dedicated WhatsApp channel. 

It is designed to run 24/7 on an Oracle Cloud Ubuntu VM, utilizing local session storage and PM2 for background process management, ensuring zero downtime and bypassing standard free-tier cloud limits.

### 🏗️ Architecture Flow
1. **Telegram Listener (Python/Telethon):** Monitors specific Telegram channels using multiple accounts concurrently.
2. **FastAPI Core (Python):** Receives raw text, scrapes associated links, and formats the data using `openai/gpt-oss-120b` via Groq.
3. **WhatsApp Broadcaster (Node.js/Puppeteer):** Receives the formatted payload and broadcasts it to a WhatsApp channel using `whatsapp-web.js`.

---

## 🛠️ Prerequisites
* An **Oracle Cloud VM** (or any Linux VPS) running **Ubuntu**.
* **Telegram API Keys:** `API_ID` and `API_HASH` from my.telegram.org.
* **Groq API Key** for LLM processing.
* A WhatsApp account to act as the sender/broadcaster.

---

## 📂 Step 1: Server Preparation & Directory Setup

SSH into your fresh Ubuntu server and run the following commands to install the required system dependencies:

### 1. Install Node.js & PM2
```bash
# Install Node.js (v20+)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -g pm2
```

### 2. Install Python Environment
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

### 3. Install Google Chrome (Required for WhatsApp Puppeteer)
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

### 4. Create Folder Structure
Clone your repository or create the following directory structure:
```text
Job_automation/
│
├── .env                  # Master environment variables
├── requirements.txt      # Python dependencies
│
├── api/                  # FastAPI Backend
│   ├── main.py
│   └── groq_processor.py
│
├── telegram_service/     # Telegram Listeners
│   └── listener.py
│
└── whatsapp_service/     # Node.js WhatsApp Bot
    ├── index.js
    └── package.json
```

---

## 🔐 Step 2: The `.env` Configuration

Create your `.env` file in the root `Job_automation` folder:
```bash
cd ~/Job_automation
nano .env
```

Paste and fill out your variables. **Crucial:** Keep `FASTAPI_WEBHOOK` as `localhost` to ensure zero-latency internal routing.

```env
# --- WhatsApp Routing ---
FASTAPI_WEBHOOK=http://localhost:8000/webhook/job

# --- Telegram Credentials ---
TELEGRAM_BOT_TOKEN=your_bot_token_if_needed
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# --- AI & Processing ---
GROQ_API_KEY=gsk_your_groq_key_here
```

---

## 🧠 Step 3: Deploy FastAPI Backend

Navigate to the `api` directory, set up your isolated Python environment, and start the server.

```bash
cd ~/Job_automation/api
python3 -m venv venv
source venv/bin/activate

# Install dependencies (pointing to the root requirements file)
pip install -r ../requirements.txt

# FIX: Upgrade Groq and HTTPX to prevent Client.__init__() proxy errors
pip install --upgrade groq httpx

# Go back to root to start PM2
cd ~/Job_automation

# Start FastAPI explicitly with the Python interpreter
pm2 start ./api/venv/bin/python --name "fastapi" -- -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## 📡 Step 4: Deploy Telegram Listeners

Telegram requires a one-time manual login to generate permanent `.session` files. **Do not start this with PM2 first.**

```bash
cd ~/Job_automation/telegram_service

# 1. RUN MANUALLY IN FOREGROUND
../api/venv/bin/python listener.py
```
* **Action Required:** The terminal will prompt you for your phone number. Enter it (with country code), then enter the OTP sent to your Telegram app. Repeat for Account 2.
* Once you see `✅ Both Telegram Accounts are Ready`, press **Ctrl + C** to stop the manual process.

```bash
# 2. START WITH PM2
pm2 start ../api/venv/bin/python --name "telegram-bot" -- listener.py
```

---

## 🟢 Step 5: Deploy WhatsApp Broadcaster

Navigate to the Node.js service, install dependencies, and start the bot.

```bash
cd ~/Job_automation/whatsapp_service
npm install whatsapp-web.js qrcode-terminal express axios node-cron dotenv

# Start with PM2
pm2 start index.js --name "whatsapp-bot"
```

### WhatsApp Bot Features (`index.js` highlights):
* **LocalAuth:** Saves the WhatsApp session directly to `./.wwebjs_auth` (No MongoDB required).
* **Puppeteer Optimizations:** Uses flags like `--disable-dev-shm-usage` and `--no-sandbox` for low-memory VPS environments.
* **Self-Healing Cron Job:** Uses `node-cron` to execute `process.exit(0)` every 3 hours. PM2 instantly restarts it, preventing the infamous Puppeteer "Detached Frame" memory leak.

**First Login:**
Run `pm2 logs whatsapp-bot` to view the QR code in your terminal. Scan it with your WhatsApp app. Once connected, it will permanently save the session.

---

## 🛡️ Step 6: Finalize Automation

To ensure your entire pipeline survives a server reboot (e.g., Oracle maintenance):

```bash
# Save the current list of running processes
pm2 save

# Generate a startup script for your OS
pm2 startup
```
*(Copy the command PM2 outputs at the bottom of the screen and run it).*

---

## 🧰 Maintenance Cheat Sheet

You can now disconnect from your server. If you ever need to check on the system, use these PM2 commands:

* **View running services:** `pm2 status`
* **View all live logs:** `pm2 logs`
* **View specific logs:** `pm2 logs fastapi` (or `whatsapp-bot`, `telegram-bot`)
* **Clear old error logs:** `pm2 flush`
* **Restart a service:** `pm2 restart telegram-bot`
* **Restart everything:** `pm2 restart all`
