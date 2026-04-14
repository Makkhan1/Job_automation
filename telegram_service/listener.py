from telethon import TelegramClient, events
import requests
import asyncio

# --- CONFIGURATION FOR ACCOUNT 1 ---
API_ID_1 = '36938322'
API_HASH_1 = '3fc97cc276641c91a217ad6f8d8c10f1'
SESSION_NAME_1 = 'session_account_1' # Creates a file named session_account_1.session

# --- CONFIGURATION FOR ACCOUNT 2 ---
API_ID_2 = '35525057'
API_HASH_2 = '5b67fa612789dae560871a08019402f4'
SESSION_NAME_2 = 'session_account_2' # Creates a file named session_account_2.session

# Replace with the exact Chat IDs or Usernames you want to listen to.
ALLOWED_CHATS = [
    '@TECHUPRISE_UPDATES',      # Example Group ID
    '@JOBSVILLAA',
    '@OCEANOFJOBS',   # Example Channel Username
    '@INTERNFREAK',
]

FASTAPI_WEBHOOK = 'http://localhost:8000/webhook/job'

# 1. Initialize both Telegram Clients
client1 = TelegramClient(SESSION_NAME_1, API_ID_1, API_HASH_1)
client2 = TelegramClient(SESSION_NAME_2, API_ID_2, API_HASH_2)

# 2. Shared function to process messages so we don't repeat code
async def process_incoming_message(event, account_identifier):
    sender = await event.get_sender()
    
    sender_name = getattr(sender, 'title', getattr(sender, 'username', getattr(sender, 'first_name', 'Unknown')))
    
    if event.is_channel:
        source_type = "Channel"
    elif event.is_group:
        source_type = "Group"
    else:
        source_type = "Contact"

    print(f"📩 Valid message from {sender_name} [via {account_identifier}]")

    payload = {
        "source_type": source_type,
        "platform": "Telegram",
        "sender_name": sender_name,
        "raw_text": event.raw_text
    }

    try:
        await asyncio.to_thread(requests.post, FASTAPI_WEBHOOK, json=payload, timeout=5)
        print(f"✅ Forwarded to FastAPI Core ({account_identifier}).")
    except Exception as e:
        print(f"❌ Failed to forward to FastAPI: {e}")

# 3. Attach the event listeners to BOTH clients
@client1.on(events.NewMessage(chats=ALLOWED_CHATS))
async def handler1(event):
    await process_incoming_message(event, "Account 1")

@client2.on(events.NewMessage(chats=ALLOWED_CHATS))
async def handler2(event):
    await process_incoming_message(event, "Account 2")

# 4. Run both clients concurrently
async def main():
    print("🚀 Starting Telegram Listeners...")
    
    # This will prompt you for the OTP for Account 1, then Account 2
    await client1.start()
    await client2.start()
    
    print("✅ Both Telegram Accounts are Ready and Connected!")
    
    # asyncio.gather keeps both clients running in the background simultaneously
    await asyncio.gather(
        client1.run_until_disconnected(),
        client2.run_until_disconnected()
    )

if __name__ == '__main__':
    asyncio.run(main())