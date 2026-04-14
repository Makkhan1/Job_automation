import requests
import os

# --- TELEGRAM CONFIGURATION ---
# Replace these with your actual Bot token and Channel ID later
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
TELEGRAM_TARGET_CHANNEL = os.getenv("TELEGRAM_TARGET_CHANNEL", "PASTE_YOUR_CHANNEL_ID_HERE") 

# --- WHATSAPP CONFIGURATION ---
WHATSAPP_URL = "http://localhost:3000/send"

def broadcast_job(formatted_job_text):
    """Sends the formatted text to both WhatsApp and Telegram"""
    
    # 1. Send to WhatsApp 
    try:
        requests.post(WHATSAPP_URL, json={"text": formatted_job_text}, timeout=10)
        print("✅ Successfully forwarded to WhatsApp Channel!")
    except Exception as e:
        print(f"❌ Failed to send to WhatsApp: {e}")

    # 2. Send to Telegram
    try:
        # Only try to send if you have actually pasted a real token
        if TELEGRAM_BOT_TOKEN != "PASTE_YOUR_BOT_TOKEN_HERE":
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            telegram_payload = {
                "chat_id": TELEGRAM_TARGET_CHANNEL,
                "text": formatted_job_text,
                "parse_mode": "HTML" 
            }
            requests.post(telegram_url, json=telegram_payload, timeout=10)
            print("✅ Successfully forwarded to Telegram Channel!")
        else:
            print("⚠️ Telegram broadcast skipped (Token not configured yet).")
    except Exception as e:
        print(f"❌ Failed to send to Telegram: {e}")